from mycroft import MycroftSkill, intent_file_handler


class AbcAustralia(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('australia.abc.intent')
    def handle_australia_abc(self, message):
        station = message.data.get('station')

        self.speak_dialog('australia.abc', data={
            'station': station
        })


def create_skill():
    return AbcAustralia()

