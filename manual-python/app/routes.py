"""HTTP routes for the Banking API.

These are intentionally small route handlers that delegate business logic
to the `services` layer. Responses are shaped to be friendly and
consistent with the Java API contract.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
import json
from .db import get_db
from .schemas import UserRegister
from .services import (
    register_user,
    login,
    create_pin,
    verify_pin_and_deposit,
    verify_pin_and_withdraw,
    verify_pin_and_transfer,
    list_transactions,
    is_pin_created,
    update_pin,
    dashboard_user,
    dashboard_account,
    logout_user,
)

router = APIRouter()


@router.post("/api/users/register")
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    res, code = await register_user(
        db,
        payload.name,
        payload.email,
        payload.password,
        payload.phone_number,
        payload.address,
        payload.country_code,
    )
    if code >= 400:
        # services returns {'error': ...}
        raise HTTPException(status_code=code, detail=res.get("error"))
    # return full success body matching Java API
    return res


@router.post("/api/users/login")
async def login_route(request: Request, db: AsyncSession = Depends(get_db)):
    # Parse login payload manually to reject duplicate/extra keys exactly.
    raw = await request.body()
    if not raw or not raw.strip():
        raise HTTPException(
            status_code=400,
            detail={"error": "Malformed JSON or missing request body"},
        )

    duplicates = []

    def _pairs_hook(pairs):
        obj = {}
        for k, v in pairs:
            if k in obj:
                duplicates.append(k)
            obj[k] = v
        return obj

    try:
        data = json.loads(raw, object_pairs_hook=_pairs_hook)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail={"error": "Malformed JSON or missing request body"},
        )

    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail={"error": "Invalid request structure"})
    if duplicates:
        raise HTTPException(status_code=400, detail={"error": "Invalid request structure"})

    allowed = {"identifier", "password"}
    extras = [k for k in data.keys() if k not in allowed]
    if extras:
        # Java behavior: unknown fields are explicit; duplicate required-key form is invalid structure.
        if len(extras) == 1:
            raise HTTPException(
                status_code=400,
                detail={"error": f"Extra field detected: {extras[0]}"},
            )
        raise HTTPException(status_code=400, detail={"error": "Invalid request structure"})

    identifier = data.get("identifier")
    password = data.get("password")
    if identifier is None or str(identifier).strip() == "":
        raise HTTPException(
            status_code=400,
            detail={"errors": {"identifier": "Identifier must not be empty"}},
        )
    if password is None or str(password).strip() == "":
        raise HTTPException(
            status_code=400,
            detail={"errors": {"password": "Password must not be empty"}},
        )

    # accepts 'identifier' per Java API
    res, code = await login(db, str(identifier), str(password))
    if code >= 400:
        raise HTTPException(status_code=code, detail=res.get("error"))
    return res


@router.post("/api/account/pin/create")
async def pin_create(request: Request, db: AsyncSession = Depends(get_db)):
    # token from header
    auth = request.headers.get("authorization", "")
    token = auth.split(" ")[-1] if auth else ""
    from .auth import decode_token

    data = decode_token(token)
    acc = data.get("sub")
    if not acc:
        raise HTTPException(
            status_code=401, detail={"error": "Missing or invalid token"}
        )

    raw = await request.body()
    if not raw or not raw.strip():
        raise HTTPException(
            status_code=400,
            detail={"error": "Malformed JSON or missing request body"},
        )
    try:
        body = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail={"error": "Malformed JSON or missing request body"},
        )

    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail={"error": "Invalid request structure"})

    allowed = {"pin", "password"}
    extras = [k for k in body.keys() if k not in allowed]
    if extras:
        raise HTTPException(
            status_code=400,
            detail={"error": f"Extra field detected: {extras[0]}"},
        )

    pin = body.get("pin")
    password = body.get("password")

    missing_pin = pin is None or str(pin).strip() == ""
    missing_password = password is None or str(password).strip() == ""

    if missing_pin and missing_password:
        raise HTTPException(
            status_code=400,
            detail={
                "errors": {
                    "pin": "PIN cannot be empty",
                    "password": "Password cannot be empty",
                }
            },
        )
    if missing_password:
        raise HTTPException(status_code=401, detail={"error": "Password cannot be empty"})
    if missing_pin:
        raise HTTPException(status_code=400, detail={"error": "PIN cannot be empty"})

    if not str(pin).isdigit() or len(str(pin)) != 4:
        raise HTTPException(status_code=400, detail={"error": "PIN must be exactly 4 digits"})

    res, code = await create_pin(db, acc, str(password), str(pin))
    if code >= 400:
        raise HTTPException(status_code=code, detail=res.get("error"))
    return res


@router.post("/api/account/deposit")
async def deposit(request: Request, db: AsyncSession = Depends(get_db)):
    raw = await request.body()
    if not raw or not raw.strip():
        raise HTTPException(
            status_code=400,
            detail={"error": "Malformed JSON or missing request body"},
        )
    try:
        body = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail={"error": "Malformed JSON or missing request body"},
        )

    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail={"error": "Invalid request structure"})

    allowed = {"pin", "amount"}
    extras = [k for k in body.keys() if k not in allowed]
    if extras:
        raise HTTPException(
            status_code=400,
            detail={"error": f"Extra field detected: {extras[0]}"},
        )

    pin = body.get("pin")
    amount = body.get("amount")

    missing_pin = pin is None or str(pin).strip() == ""
    missing_amount = amount is None or str(amount).strip() == ""

    if missing_pin and missing_amount:
        raise HTTPException(
            status_code=400,
            detail={
                "errors": {
                    "pin": "PIN cannot be empty",
                    "amount": "Amount cannot be empty",
                }
            },
        )
    if missing_pin:
        raise HTTPException(status_code=400, detail={"errors": {"pin": "PIN cannot be empty"}})
    if missing_amount:
        raise HTTPException(
            status_code=400,
            detail={"errors": {"amount": "Amount cannot be empty"}},
        )

    try:
        amount_val = float(amount)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail={"error": "Invalid request structure"})

    if amount_val <= 0:
        raise HTTPException(status_code=400, detail={"error": "Amount must be greater than 0"})
    if int(amount_val) % 100 != 0:
        raise HTTPException(status_code=400, detail={"error": "Amount must be in multiples of 100"})

    auth = request.headers.get("authorization", "")
    token = auth.split(" ")[-1] if auth else ""
    from .auth import decode_token

    data = decode_token(token)
    acc = data.get("sub")
    if not acc:
        raise HTTPException(
            status_code=401, detail={"error": "Missing or invalid token"}
        )
    res, code = await verify_pin_and_deposit(db, acc, str(pin), amount_val)
    if code >= 400:
        raise HTTPException(status_code=code, detail=res.get("error"))
    return res


@router.post("/api/account/withdraw")
async def withdraw(request: Request, db: AsyncSession = Depends(get_db)):
    raw = await request.body()
    if not raw or not raw.strip():
        raise HTTPException(
            status_code=400,
            detail={"error": "Malformed JSON or missing request body"},
        )
    try:
        body = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail={"error": "Malformed JSON or missing request body"},
        )

    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail={"error": "Invalid request structure"})

    allowed = {"pin", "amount"}
    extras = [k for k in body.keys() if k not in allowed]
    if extras:
        raise HTTPException(
            status_code=400,
            detail={"error": f"Extra field detected: {extras[0]}"},
        )

    pin = body.get("pin")
    amount = body.get("amount")

    missing_pin = pin is None or str(pin).strip() == ""
    missing_amount = amount is None or str(amount).strip() == ""

    if missing_pin and missing_amount:
        raise HTTPException(
            status_code=400,
            detail={
                "errors": {
                    "pin": "PIN cannot be empty",
                    "amount": "Amount cannot be empty",
                }
            },
        )
    if missing_pin:
        raise HTTPException(status_code=400, detail={"errors": {"pin": "PIN cannot be empty"}})
    if missing_amount:
        raise HTTPException(
            status_code=400,
            detail={"errors": {"amount": "Amount cannot be empty"}},
        )

    try:
        amount_val = float(amount)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail={"error": "Invalid request structure"})

    if amount_val <= 0:
        raise HTTPException(status_code=400, detail={"error": "Amount must be greater than 0"})
    if int(amount_val) % 100 != 0:
        raise HTTPException(status_code=400, detail={"error": "Amount must be in multiples of 100"})

    auth = request.headers.get("authorization", "")
    token = auth.split(" ")[-1] if auth else ""
    from .auth import decode_token

    data = decode_token(token)
    acc = data.get("sub")
    if not acc:
        raise HTTPException(
            status_code=401, detail={"error": "Missing or invalid token"}
        )
    res, code = await verify_pin_and_withdraw(db, acc, str(pin), amount_val)
    if code >= 400:
        raise HTTPException(status_code=code, detail=res.get("error"))
    return res


@router.post("/api/account/fund-transfer")
async def transfer(request: Request, db: AsyncSession = Depends(get_db)):
    raw = await request.body()
    if not raw or not raw.strip():
        raise HTTPException(
            status_code=400,
            detail={"error": "Malformed JSON or missing request body"},
        )
    try:
        body = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail={"error": "Malformed JSON or missing request body"},
        )

    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail={"error": "Invalid request structure"})

    allowed = {"pin", "amount", "targetAccountNumber", "target_account_number"}
    extras = [k for k in body.keys() if k not in allowed]
    if extras:
        raise HTTPException(
            status_code=400,
            detail={"error": f"Extra field detected: {extras[0]}"},
        )

    pin = body.get("pin")
    amount = body.get("amount")
    target = (
        body.get("targetAccountNumber")
        if "targetAccountNumber" in body
        else body.get("target_account_number")
    )

    missing_pin = pin is None or str(pin).strip() == ""
    missing_amount = amount is None or str(amount).strip() == ""
    missing_target = target is None or str(target).strip() == ""

    if missing_pin or missing_amount or missing_target:
        errors = {}
        # Keep Java ordering from provided sample: target, pin, amount
        if missing_target:
            errors["targetAccountNumber"] = "Target account number cannot be empty"
        if missing_pin:
            errors["pin"] = "PIN cannot be empty"
        if missing_amount:
            errors["amount"] = "Amount cannot be empty"
        raise HTTPException(status_code=400, detail={"errors": errors})

    try:
        amount_val = float(amount)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail={"error": "Invalid request structure"})

    if amount_val <= 0:
        raise HTTPException(
            status_code=400,
            detail={"errors": {"amount": "Amount must be greater than 0"}},
        )
    if int(amount_val) % 100 != 0:
        raise HTTPException(status_code=400, detail={"error": "Amount must be in multiples of 100"})

    auth = request.headers.get("authorization", "")
    token = auth.split(" ")[-1] if auth else ""
    from .auth import decode_token

    data = decode_token(token)
    acc = data.get("sub")
    if not acc:
        raise HTTPException(
            status_code=401, detail={"error": "Missing or invalid token"}
        )
    res, code = await verify_pin_and_transfer(
        db, acc, str(pin), str(target), amount_val
    )
    if code >= 400:
        raise HTTPException(status_code=code, detail=res.get("error"))
    return res


@router.get("/api/account/transactions")
async def transactions(request: Request, db: AsyncSession = Depends(get_db)):
    auth = request.headers.get("authorization", "")
    token = auth.split(" ")[-1] if auth else ""
    from .auth import decode_token

    data = decode_token(token)
    acc = data.get("sub")
    if not acc:
        raise HTTPException(
            status_code=401, detail={"error": "Missing or invalid token"}
        )
    res, code = await list_transactions(db, acc)
    if code >= 400:
        raise HTTPException(status_code=code, detail=res.get("error"))
    # services returns serialized transactions and msg
    return res


@router.get("/api/account/pin/check")
async def pin_check(request: Request, db: AsyncSession = Depends(get_db)):
    auth = request.headers.get("authorization", "")
    token = auth.split(" ")[-1] if auth else ""
    from .auth import decode_token

    data = decode_token(token)
    acc = data.get("sub")
    if not acc:
        raise HTTPException(
            status_code=401, detail={"error": "Missing or invalid token"}
        )
    res, code = await is_pin_created(db, acc)
    if code >= 400:
        raise HTTPException(status_code=code, detail=res.get("error"))
    return res


@router.post("/api/account/pin/update")
async def pin_update(request: Request, db: AsyncSession = Depends(get_db)):
    raw = await request.body()
    if not raw or not raw.strip():
        raise HTTPException(
            status_code=400,
            detail={"error": "Malformed JSON or missing request body"},
        )
    try:
        body = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail={"error": "Malformed JSON or missing request body"},
        )

    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail={"error": "Invalid request structure"})

    allowed = {"oldPin", "newPin", "password", "old_pin", "new_pin"}
    extras = [k for k in body.keys() if k not in allowed]
    if extras:
        raise HTTPException(
            status_code=400,
            detail={"error": f"Extra field detected: {extras[0]}"},
        )

    old_pin = body.get("oldPin") if "oldPin" in body else body.get("old_pin")
    new_pin = body.get("newPin") if "newPin" in body else body.get("new_pin")
    password = body.get("password")

    errors = {}
    if password is None or str(password).strip() == "":
        errors["password"] = "Password cannot be empty"
    if old_pin is None or str(old_pin).strip() == "":
        errors["oldPin"] = "Old PIN cannot be empty"
    if new_pin is None or str(new_pin).strip() == "":
        errors["newPin"] = "New PIN cannot be empty"
    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})

    if not str(old_pin).isdigit() or len(str(old_pin)) != 4:
        raise HTTPException(
            status_code=400,
            detail={"errors": {"oldPin": "PIN must be exactly 4 digits"}},
        )
    if not str(new_pin).isdigit() or len(str(new_pin)) != 4:
        raise HTTPException(
            status_code=400,
            detail={"errors": {"newPin": "PIN must be exactly 4 digits"}},
        )

    auth = request.headers.get("authorization", "")
    token = auth.split(" ")[-1] if auth else ""
    from .auth import decode_token

    data = decode_token(token)
    acc = data.get("sub")
    if not acc:
        raise HTTPException(
            status_code=401, detail={"error": "Missing or invalid token"}
        )
    res, code = await update_pin(db, acc, str(password), str(old_pin), str(new_pin))
    if code >= 400:
        raise HTTPException(status_code=code, detail=res.get("error"))
    return res


@router.get("/api/dashboard/user")
async def dashboard_user_route(request: Request, db: AsyncSession = Depends(get_db)):
    auth = request.headers.get("authorization", "")
    token = auth.split(" ")[-1] if auth else ""
    from .auth import decode_token

    data = decode_token(token)
    acc = data.get("sub")
    if not acc:
        raise HTTPException(
            status_code=401, detail={"error": "Missing or invalid token"}
        )
    res, code = await dashboard_user(db, acc)
    if code >= 400:
        raise HTTPException(status_code=code, detail=res.get("error"))
    return res


@router.get("/api/dashboard/account")
async def dashboard_account_route(request: Request, db: AsyncSession = Depends(get_db)):
    auth = request.headers.get("authorization", "")
    token = auth.split(" ")[-1] if auth else ""
    from .auth import decode_token

    data = decode_token(token)
    acc = data.get("sub")
    if not acc:
        raise HTTPException(
            status_code=401, detail={"error": "Missing or invalid token"}
        )
    res, code = await dashboard_account(db, acc)
    if code >= 400:
        raise HTTPException(status_code=code, detail=res.get("error"))
    return res


@router.post("/api/users/logout")
async def logout_route(request: Request, db: AsyncSession = Depends(get_db)):
    auth = request.headers.get("authorization", "")
    token = auth.split(" ")[-1] if auth else ""
    if not token:
        raise HTTPException(status_code=401, detail={"error": "Missing token"})
    res, code = await logout_user(db, token)
    if code >= 400:
        raise HTTPException(status_code=code, detail=res.get("error"))
    return res
