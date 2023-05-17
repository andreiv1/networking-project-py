import json


class Response:
    def __init__(self, message):
        self.message = message

    @staticmethod
    def from_json(data):
        data = json.loads(data)
        if data["type"] != "response":
            return None
        return Response(data["message"])

    def get_message(self):
        return self.message

    def __str__(self):
        response_dict = {
            'type': "response",
            'message': self.message
        }
        return json.dumps(response_dict, default=str)
class Request:
    def __init__(self, command, params=None):
        self.command = command
        self.params = params

    def get_command(self):
        return self.command

    def get_params(self):
        return self.params

    @staticmethod
    def from_json(data):
        data = json.loads(data)
        if data["type"] != "request":
            return None
        return Request(data["command"], data["params"])

    def __str__(self):
        request_dict = {
            'type': "request",
            'command': self.command,
            'params': self.params if self.params is not None else ""
        }
        return json.dumps(request_dict,default=str)
class Notification:
    def __init__(self, message, action=None):
        self.action = action
        self.message = message

    def get_message(self):
        return self.message

    def get_action(self):
        return self.action
    @staticmethod
    def from_json(data):
        data = json.loads(data)
        if data["type"] != "notification":
            return None
        return Notification(data["message"], data["action"])

    def __str__(self):
        notification_dict = {
            'type': "notification",
            'message': self.message,
            'action': self.action if self.action is not None else ""
        }
        return json.dumps(notification_dict,default=str)
