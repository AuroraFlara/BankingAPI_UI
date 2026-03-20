To Start Up project

## 1: Update application.properties / env
    #For Java
    spring.datasource.username=${DB_USERNAME:"YOUR USERNAME"}
    spring.datasource.password=${DB_PASSWORD:"YOUR PASSWORD"}

    # Run the command in your terminal:openssl rand -base64 64 | tr -d '\n' 
    # then copy the output and paste it as the default value for jwt.secret
    jwt.secret="YOUR JWT PASSWORD"

    #For Python
    MYSQL_USER= YOUR USERNAME
    MYSQL_PASSWORD=YOUR PASSWORD
    MYSQL_DB=bankingapp_new (change if needed)

    # Run the command in your terminal:openssl rand -base64 64 | tr -d '\n' 
    # then copy the output and paste it as the default value for jwt.secret
    JWT_SECRET="YOUR JWT PASSWORD"

## 2: Create environment
    cd bankingapi_ui
    python3 -m venv venv

## 3: Activate the Environment
    # For Mac/Linux:
    source venv/bin/activate

    # For window:
    venv\Scripts\activate.bat

## 4: Download modules in requirements
    pip install -r requirements.txt

## 5: Navigate to Experiment you will like to test
    cd java-baseline / cd manual-python / cd claude-assisted / cd claude-fullgenai / cd codex-assisted / cd codex-fullgenai

## 6: Start BankingAPI project
    
### 6.1: For Java Baseline
    # Install homebrew if not installed
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    brew install maven
    mvn -v

    # Install Java 17
    brew install openjdk@17

    # Switch terminal to use
    export JAVA_HOME=`/usr/libexec/java_home -v 17`

    # Verify java version, it should now say 17.x.x
    java -version

    # Ensure Build Success
    mvn clean compile
    mvn clean install -DskipTests
    
    # Run Java project
    mvn spring-boot:run
    mvn clean spring-boot:run

    # if error run
    mvn clean compile -DargLine="--add-opens java.base/java.lang=ALL-UNNAMED --add-opens jdk.compiler/com.sun.tools.javac.code=ALL-UNNAMED"

### 6.2: For python code
    # Install modules in requirements.txt
    cd BankingAPI_UI
    pip install -r requirements.txt

    # Locate to specified python expriment folder
    cd manual-python
    uvicorn app.main:app --host 127.0.0.1 --port 8005 --reload

    cd claude-assisted
    uvicorn app.main:app --host 127.0.0.1 --port 8004 --reload

    cd claude-fullgenai
    uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload

    cd codex-assisted
    uvicorn app.main:app --host 127.0.0.1 --port 8003 --reload

    cd codex-fullgenai
    uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload


## 7: Start BankingAPI UI (Please open 2nd terminal)
    #Locate to folder ui
    cd ui

    #Launch the UI
    streamlit run app_ui.py
    