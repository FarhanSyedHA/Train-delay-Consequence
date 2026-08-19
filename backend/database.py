# a class to create database object to make connect, query read and write operations. 
import os
import logging
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from neo4j import GraphDatabase, Driver, exceptions

load_dotenv()

logger = logging.getLogger("uvicorn")


class DatabaseConnection:
    _driver: Optional[Driver] = None

    @classmethod
    def get_driver(cls) -> Driver:
        if cls._driver is None:
            uri = os.getenv("COGNODB_URI")
            user = os.getenv("COGNODB_USER", "cognodb")
            password = os.getenv("COGNODB_PASSWORD")

            if not uri or not password:
                raise ValueError("COGNODB_URI and COGNODB_PASSWORD must be configured in .env")

            try:
                cls._driver = GraphDatabase.driver(
                    uri,
                    auth=(user, password),
                    max_connection_lifetime=3600,
                    max_connection_pool_size=50,
                    connection_acquisition_timeout=10.0
                )
                cls._driver.verify_connectivity()
                logger.info("Connected successfully to CognoDB Cloud.")
            except exceptions.Neo4jError as e:
                logger.error(f"Failed to connect or authenticate with CognoDB Cloud: {e}")
                raise
        return cls._driver

    @classmethod
    def close(cls):
        if cls._driver is not None:
            cls._driver.close()
            cls._driver = None
            logger.info("CognoDB connection pool closed.")


def execute_read_query(query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Executes a managed read Cypher transaction with automatic retries."""
    driver = DatabaseConnection.get_driver()
    with driver.session() as session:
        def _read_tx(tx):
            result = tx.run(query, parameters or {})
            return [record.data() for record in result]
        return session.execute_read(_read_tx)


def execute_write_query(query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Executes a managed write Cypher transaction with automatic retries."""
    driver = DatabaseConnection.get_driver()
    with driver.session() as session:
        def _write_tx(tx):
            result = tx.run(query, parameters or {})
            return [record.data() for record in result]
        return session.execute_write(_write_tx)