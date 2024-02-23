import requests
import irc.bot
import sys
import openai
from openai import OpenAI


class TwitchBot(irc.bot.SingleServerIRCBot):
    def __init__(self, username, client_id, token, channel, openai_api_key):

        self.gpt_client = OpenAI(api_key=openai_api_key)

        self.client_id = client_id
        self.token = token
        self.channel = '#' + channel

        # Use the Twitch Helix API to get the channel ID
        url = f'https://api.twitch.tv/helix/users?login={channel}'
        headers = {
            'Client-ID': client_id,
            'Authorization': f'Bearer {token}',  # Helix API uses Bearer token for authorization
        }
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            r_json = r.json()
            self.channel_id = r_json['data'][0]['id']  # Note the different JSON structure in Helix API
        else:
            print(f"Failed to obtain channel ID. Status code: {r.status_code}")
            sys.exit(1)
        # Connect to Twitch IRC
        server = 'irc.chat.twitch.tv'
        port = 6667
        print(f'Connecting to {server} on port {port}...')
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, f'oauth:{token}')], username, username)

    """
    This method is called when 
    """

    def on_welcome(self, connection, event):
        print(f"Joining {self.channel}")
        connection.cap('REQ', ':twitch.tv/membership')
        connection.cap('REQ', ':twitch.tv/tags')
        connection.cap('REQ', ':twitch.tv/commands')
        connection.join(self.channel)
        print(f"Joined {self.channel}")

    """
    This method is called when a new message is published on the twitch chat.
    """

    def on_pubmsg(self, connection, event):
        # Check if the message is "!hi" and respond
        if event.arguments[0] == "!hi":
            self.do_command(event, "!hi")
        elif event.arguments[0] == "!ask who is practicex":
            connection.privmsg(self.channel, "PracticeX is a famous Twitch streamer who usually streams StarCraft II.")
        elif event.arguments[0].startswith('!ask'):
            print("on pubmsg")
            self.do_command(event, "!ask")

    def do_command(self, event, cmd):
        if cmd == "!hi":
            self.connection.privmsg(self.channel, "Hello! How are you?")
        elif cmd == '!ask':
            prompt = event.arguments[0][5:]
            response = self.generate_chatgpt_response(prompt)
            if response:
                self.connection.privmsg(self.channel, response)

    def generate_chatgpt_response(self, prompt):
        concise_prompt = f"{prompt}, please respond with less than 500 characters"

        try:
            response = self.gpt_client.chat.completions.create(
                model="gpt-3.5-turbo",  # Change ChatGPT model here.
                messages=[
                    {"role": "user", "content": concise_prompt}
                ],
                max_tokens=60,  # Adjust to encourage conciseness, experiment as needed
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating response: {e}")
            return None


if __name__ == "__main__":
    # Add appropriate values below.
    client_id = ''  # The bot twitch account client ID. Obtained from twitch developer console.
    bot_username = ''  # The bot's twitch username.
    target_channel = ''  # The channel that the bot is going to join.
    token = ''  # Bot twitch account OAuth token. can be generated using https://twitchtokengenerator.com/
    openai_api_key = ''  # Add Open AI api key if using chatgpt integration.

    #Initialize and start bot.
    bot = TwitchBot(bot_username, client_id, token, target_channel, openai_api_key)
    bot.start()

