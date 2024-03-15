from typing import Optional, Union

from streamsync.core import base_component_tree
from streamsync.core_ui import (Component, SessionComponentTree,
                                UIError, current_parent_container)


class StreamsyncUI:
    """Provides mechanisms to manage and manipulate UI components within a
    Streamsync session.

    This class offers context managers and methods to dynamically create, find,
    and organize UI components based on a structured component tree.
    """

    def __init__(self, component_tree: Union[SessionComponentTree, None] = None):
        self.component_tree = component_tree or base_component_tree
        self.root_component = self.component_tree.get_component('root')

    def __enter__(self):
        return self

    def __exit__(self, *args):
        ...

    @staticmethod
    def assert_in_container():
        container = current_parent_container.get(None)
        if container is None:
            raise UIError("A component can only be created inside a container")

    @property
    def root(self) -> Component:
        if not self.root_component:
            raise RuntimeError("Failed to acquire root component")
        return self.root_component

    def find(self, component_id: str) \
            -> Component:
        """
        Retrieves a component by its ID from the current session's component tree.

        This method searches for a component with the given ID within the
        application's UI structure. If the component is found, it is returned
        for further manipulation or inspection.

        :param component_id: The unique identifier of the component to find.
        :type component_id: str
        :return: The found component with the specified ID.
        :rtype: Component
        :raises RuntimeError: If no component with the specified ID is found
        in the current session's component tree.

        **Example**::

        >>> my_component = ui.find("my-component-id")
        >>> print(my_component.properties)
        """
        component = self.component_tree.get_component(component_id)
        if component is None:
            raise RuntimeError(f"Component {component_id} not found")
        return component

    def refresh_with(self, component_id: str):
        """
        Clears the existing children of a container component and sets it up to
        accept new components. This method is designed to refresh the specified
        container with new content specified in the subsequent block.

        :param component_id: The unique identifier of the container component
                             to be refreshed.
        :type component_id: str
        :raises RuntimeError: If no component with the specified ID is found
        in the current session's component tree.

        .. note:: Upon invocation, this method clears all children of the
        specified container component to prepare for new content. If no new
        components are added within the context block, the container will
        simply be emptied.

        **Example**:
        >>> with ui.refresh_with(id="my-container"):
        >>>     ui.Text({"text": "New content"}, id="new-content-1")
        >>>     ui.Button({"text": "Click me"}, id="new-button-1")

        This method can also be used to clear existing children without adding
        new components:
        >>> with ui.refresh_with(id="my-container"):
        >>>     pass
        """
        component = self.find(component_id)
        if not component:
            raise RuntimeError(f"Component {component_id} not found")

        # Clear the children of the specified component.
        self.component_tree.clear_children(component_id)

        return component

    def _prepare_handlers(self, raw_handlers: Optional[dict]):
        handlers = {}
        if raw_handlers is not None:
            for event, handler in raw_handlers.items():
                if callable(handler):
                    handlers[event] = handler.__name__
                else:
                    handlers[event] = handler
        return handlers

    def _prepare_binding(self, raw_binding):
        # TODO
        return raw_binding

    def _create_component(
            self,
            component_type: str,
            **kwargs) -> Component:
        parent_container = current_parent_container.get(None)
        if kwargs.get("id", False) is None:
            kwargs.pop("id")

        if kwargs.get("position", False) is None:
            kwargs.pop("position")

        if kwargs.get("parentId", False) is None:
            kwargs.pop("parentId")

        if "parentId" in kwargs:
            parent_id = kwargs.pop("parentId")
        else:
            parent_id = "root" if not parent_container else parent_container.id

        position: Optional[int] = kwargs.pop("position", None)
        is_positionless: bool = kwargs.pop("positionless", False)
        raw_handlers: dict = kwargs.pop("handlers", {})
        raw_binding: dict = kwargs.pop("binding", {})

        handlers = self._prepare_handlers(raw_handlers) or None
        binding = self._prepare_binding(raw_binding) or None

        component = Component(
            type=component_type,
            parentId=parent_id,
            flag="cmc",
            handlers=handlers,
            binding=binding,
            **kwargs
            )

        # We're determining the position separately
        # due to that we need to know whether ID of the component
        # is present within base component tree
        # or a session-specific one
        component.position = \
            position if position is not None else \
            self.component_tree.determine_position(
                component.id,
                parent_id,
                is_positionless=is_positionless
                )

        self.component_tree.attach(component)
        return component

    def create_container_component(self, component_type: str, **kwargs) \
            -> Component:
        container = self._create_component(component_type, **kwargs)
        return container

    def create_component(self, component_type: str, **kwargs) \
            -> Component:
        self.assert_in_container()
        component = self._create_component(component_type, **kwargs)
        return component
