# SNC-Server, an Attorney Online server
#
# Copyright (C) 2020 Hitomu
#
# Derivative of tsuserver3, an Attorney Online server. Copyright (C) 2016 argoneus <argoneuscze@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from urllib import parse
import asyncio
import discord
from discord.ext import commands
from discord.utils import escape_markdown
from discord.errors import Forbidden, HTTPException

class Bridgebot(commands.Bot):
    """
    The AO2 Discord bridge self.
    """
    def __init__(self, server, target_chanel, hub_id, area_id):
        super().__init__(command_prefix='$')
        self.server = server
        self.pending_messages = []
        self.hub_id = 0
        self.area_id = 0
        self.target_channel = ao2

    @staticmethod
    def loop_it_forever(loop):
        loop.run_forever()
        loop.close()

    async def init(self, token):
        '''Starts the actual bot'''
        print('Trying to start the Discord Bridge bot...')
        try:
            await self.start(token)
        except Exception as e:
            print(e)
            raise
    
    def queue_message(self, name, message, charname):
        base = None
        avatar_url = None
        if "base_url" in self.server.config["bridgebot"]:
            base = self.server.config["bridgebot"]["base_url"]
        if base != None:
            avatar_url = base + parse.quote("characters/" + charname + "/char_icon.png")
        self.pending_messages.append([name, message, avatar_url])

    async def on_ready(self):
        print('Discord Bridge Successfully logged in.')
        print('Username -> ' + self.user.name)
        print('ID -> ' + str(self.user.id))
        self.guild = self.guilds[0]
        self.channel = discord.utils.get(self.guild.text_channels, name=self.target_channel)
        await self.wait_until_ready()

        while True:
            if len(self.pending_messages) > 0:
                await self.send_char_message(*self.pending_messages.pop())

            await asyncio.sleep(max(0.1, self.server.config["bridgebot"]["tickspeed"]))

    async def on_message(self, message):
        # Screw these loser bots
        if message.author.bot or message.webhook_id != None:
            return
        
        if message.channel != self.channel:
            return

        if not message.content.startswith('$'):
            try:
                max_char = int(self.server.config['max_chars'])
            except:
                max_char = 256
            if len(message.clean_content) > max_char:
                await self.channel.send('Your message was too long - it was not received by the client. (The limit is 256 characters)')
                return
            self.server.send_discord_chat(message.author.name, escape_markdown(message.clean_content), self.hub_id, self.area_id)

        # await self.process_commands(message)
    
    async def send_char_message(self, name, message, avatar=None):
        webhook = https://discord.com/api/webhooks/814234992351379476/QvXqcDCI9reA33dg3UJXrm0F3jF8BsGnv4nOdouDxfoiAXi0g8-xU9KCARA4EgvH64IT
        try:
            webhooks = await self.channel.webhooks()
            for hook in webhooks:
                if hook.user == self.user or hook.name == 'SnC':
                    webhook = hook
                    break
            if webhook == None:
                webhook = await self.channel.create_webhook(name='AO2_Bridgebot')
            await webhook.send(message, username=name, avatar_url=avatar)
            print(f'[DiscordBridge] Sending message from "{name}" to "{self.channel.name}"')
        except Forbidden:
            print(f'[DiscordBridge] Insufficient permissions - couldnt send char message "{name}: {message}" with avatar "{avatar}" to "{self.channel.name}"')
        except HTTPException:
            print(f'[DiscordBridge] HTTP Failure - couldnt send char message "{name}: {message}" with avatar "{avatar}" to "{self.channel.name}"')