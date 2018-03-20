class SecureSettings():
     # These two values are very important and should not be stored in GIT. As
     # such this file 'secure.py' is listed in .git ignore. 
    SECRET_KEY = "AVeryPrivateSecret"
    SECURITY_PASSWORD_SALT = "jdsfhbasdjkfhasldjkfhasiuy324783y58934"
    