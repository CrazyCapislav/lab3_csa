class MUX:
    """Базовый класс для всех MUX"""

    def __init__(self):
        self.state = None

    def handle_input(self, state):
        """Обрабатывает входное значение, строка или объект"""
        if isinstance(state, str):
            self.set_state(state)
        elif isinstance(state, MUX):
            self.state = state.state
        else:
            raise TypeError({state})

    def set_state(self, state):
        raise NotImplementedError("Этот метод должен быть реализован в подклассе.")

    def switch_state(self):
        raise NotImplementedError("Этот метод должен быть реализован в подклассе.")


class AccMux(MUX):
    def __init__(self):
        super().__init__()
        self.state = "ALU"  # Начальное состояние по умолчанию

    def set_state(self, state):
        # Добавляем "NONE" как допустимое состояние
        if state in ["ALU", "MEM", "NONE"]:
            self.state = state
        else:
            raise ValueError(f"Недопустимое состояние: {state}")

    def switch_state(self):
        """Переключает состояние между ALU и MEM"""
        self.state = "ALU" if self.state == "MEM" else "MEM"


class DRMux(MUX):
    def __init__(self):
        super().__init__()
        self.state = "MEM"  # Начальное состояние по умолчанию

    def set_state(self, state):
        # Добавляем "NONE" как допустимое состояние
        if state in ["CU", "MEM", "NONE"]:
            self.state = state
        else:
            raise ValueError(f"Недопустимое состояние: {state}")

    def switch_state(self):
        """Переключает состояние между CU и MEM"""
        self.state = "CU" if self.state == "MEM" else "MEM"


class ProgramCounterMux(MUX):
    def __init__(self):
        super().__init__()
        self.state = "INC"  # Начальное состояние по умолчанию

    def set_state(self, state):
        if state in ["INC", "MEM"]:
            self.state = state
        else:
            raise ValueError(f"Недопустимое состояние: {state}")

    def switch_state(self):
        """Переключает состояние между INC и MEM"""
        self.state = "INC" if self.state == "MEM" else "MEM"


class DAMux(MUX):
    def __init__(self):
        super().__init__()
        self.state = "CU"

    def set_state(self, state):
        if state in ["DR", "CU"]:
            self.state = state
        else:
            raise ValueError(f"Недопустимое состояние: {state}")

    def switch_state(self):
        """Переключает состояние между CU и DR"""
        self.state = "CU" if self.state == "DR" else "DR"
