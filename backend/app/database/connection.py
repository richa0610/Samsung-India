from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

# URL.create safely encodes characters such as @, :, and / in database
# credentials. Building the URL with an f-string makes those characters look
# like URL delimiters and prevents the API from starting.
DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=settings.DB_USER,  
    password=settings.DB_PASSWORD,
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    database=settings.DB_NAME,
)

connect_args: dict = {"connect_timeout": 5, "read_timeout": 10, "write_timeout": 10}
if settings.DB_SSL_CA:
    connect_args["ssl"] = {"ca": settings.DB_SSL_CA}

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    # Proactively discard a pooled connection once it's this old, rather
    # than waiting to discover it's gone dead (managed MySQL providers and
    # the network path to them commonly close idle connections server-side
    # around the 5-10 minute mark - without this, reusing one of those after
    # it's silently died just hangs, since pool_pre_ping's own health-check
    # query can hang exactly the same way without the connect/read timeouts
    # above). 280s keeps every connection well under that window.
    pool_recycle=280,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()
