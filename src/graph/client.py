from typing import Any
from neo4j import GraphDatabase, Driver
from src.config import settings


class Neo4jClient:
    def __init__(
        self,
        uri: str | None = None,
        user: str | None = None,
        password: str | None = None,
    ) -> None:
        self._uri = uri or settings.neo4j_uri
        self._user = user or settings.neo4j_user
        self._password = password or settings.neo4j_password
        self._driver: Driver | None = None

    def connect(self) -> Driver:
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self._uri, auth=(self._user, self._password)
            )
        return self._driver

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def verify_connectivity(self) -> bool:
        driver = self.connect()
        driver.verify_connectivity()
        return True

    def execute_query(
        self, query: str, parameters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        driver = self.connect()
        with driver.session(database=settings.neo4j_database) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]


neo4j_client = Neo4jClient()
