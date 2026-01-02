# # app/config.py


from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = Field(..., env='DATABASE_URL')

    google_gemini_api_key: str = Field(..., env='GOOGLE_GEMINI_API_KEY')

    secret_key: str = Field(..., env='SECRET_KEY')
    algorithm: str = Field(default='HS256', env='ALGORITHM')
    access_token_expire_minutes: int = Field(..., env='ACCESS_TOKEN_EXPIRE_MINUTES')
    refresh_token_expire_minutes: int = Field(..., env='REFRESH_TOKEN_EXPIRE_MINUTES')
    otp_expire_minutes: int = Field(..., env='OTP_EXPIRE_MINUTES')

    smtp_host: str = Field(..., env='SMTP_HOST')
    smtp_port: int = Field(..., env='SMTP_PORT')
    smtp_user: str = Field(..., env='SMTP_USER')
    smtp_pass: str = Field(..., env='SMTP_PASS')

    class Config:
        env_file = ".env" 
        env_file_encoding = 'utf-8'
        # extra = 'forbid' 

settings = Settings()















# from pydantic_settings import BaseSettings

# class Settings(BaseSettings):
#     # Database
#     DATABASE_URL: str



#     # Auth
#     SECRET_KEY: str
#     ALGORITHM: str = "HS256"
#     ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
#     REFRESH_TOKEN_EXPIRE_MINUTES: int = 1440
#     OTP_EXPIRE_MINUTES: int = 20

#     # Email
#     SMTP_HOST: str
#     SMTP_PORT: int = 587
#     SMTP_USER: str
#     SMTP_PASS: str

#     class Config:
#         env_file = ".env"


# settings = Settings()