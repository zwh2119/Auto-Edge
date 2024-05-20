class Adapter:
    @staticmethod
    def done_adapter(done, t):
        if t % 100 == 0:
            return not done
        else:
            return done

    @staticmethod
    def action_adapter(a, max_action):
        """from [-1,1] to [-max,max]"""
        a[0] *= max_action[0]
        a[1] *= max_action[1]
        a[2] *= max_action[2]

        return abs(a)

    @staticmethod
    def action_adapter_reverse(act, max_action):
        # from [-max,max] to [-1,1]
        return act / max_action
