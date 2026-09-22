from dash import Dash

from loguru import logger

from abc import ABC, abstractmethod

class AbstractPage(ABC):
    def __init__(self, app: Dash, name: str, layout: list):
        self._app = app
        self._name = name
        self._layout = layout
        self._callbacks_registered = False

    @abstractmethod
    def _register_callbacks(self): ...

    def display(self):
        if not self._callbacks_registered:
            logger.info(f"Registering callbacks for {self._name} page")
            self._register_callbacks()
            self._callbacks_registered = True

        logger.info(f"Displaying {self._name} page")
        self._app.layout = self._layout