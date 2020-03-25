import discord
from time import time


class RateLimiter(object):
    # create the rate limiter
    def __init__(self, cmd_list: dict):
        self.limits = {}
        self.lastExec = {}
        for i in cmd_list:
            if i["ratelimit"]["user_dependent"]:
                exec_template = {
                    "name": i["command"],
                    "ulist": []
                }
            else:
                exec_template = {
                    "name": i["command"],
                    "timestamp": 0
                }
            self.limits[i["command"]] = RateLimit(
                i["ratelimit"]["limit"], i["ratelimit"]["user_dependent"])
            self.lastExec[i["command"]] = exec_template

    # use the ratelimiter

    def exec(self, command) -> tuple:
        user_template = {
            "user": command.invoked_by.id,
            "timestamp": 0
        }

        # is this command limited? overwrites global limis
        if self.limits[command.command].limit: 

            # the limit is per-user           
            if self.limits[command.command].user_dependent:
                last_exec = list(filter(lambda x: x[1]["user"] == command.invoked_by.id, enumerate(
                self.lastExec[command.command]["ulist"])))
                if len(last_exec) > 0:

                    if self.limits[command.command].test(int(time()), last_exec[0][1]):
                        self.lastExec[command.command]["ulist"][last_exec[0]
                                                                [0]]["timestamp"] = int(time())
                        return True
                    else:
                        return False

                
                else:
                    # set the user profile, first execution so we can let it pass
                    self.lastExec[command.command]["ulist"].append(user_template)
                    return True
            # global command limit
            else:
                last_exec = self.lastExec[command.command]
                if self.limits[command.command].test(last_exec["timestamp"]):
                    self.lastExec[command.command]["timestamp"] = int(time())
                    return True
                else:
                    return False
        else:
            return True


# rate limit object
class RateLimit(object):
    def __init__(self, limit: int, user_dependent: bool):
        self.limit = limit
        self.user_dependent = user_dependent

    def test(self, time: int, lastExec: dict) -> bool:
        if time - lastExec["timestamp"] < self.limit:
            return False
        return True

    def __str__(self) -> str:
        return f'{self.limit} - {self.user_dependent}'
