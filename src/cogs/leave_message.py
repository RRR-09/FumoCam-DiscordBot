import nextcord
from nextcord.ext import commands  # type: ignore

from utils import BotClass


class LeaveMessage(commands.Cog):
    def __init__(self, bot: BotClass):
        self.bot = bot

        self.leave_channel_name = self.bot.CFG.get("leave_channel")
        if self.leave_channel_name is None:
            print(
                "['leave_channel' not specified in config, disabling leave-message subroutine]"
            )
            return

        if self.leave_channel_name not in self.bot.channels:
            print(
                f"['{self.leave_channel_name}' not found, disabling leave-message subroutine]"
            )
            return
        self.leave_channel = self.bot.channels[self.leave_channel_name]

        self.leave_message = self.bot.CFG.get(
            "leave_message", "> {member_name} has left the server."
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member: nextcord.Member):
        member_name = f"{member.name}#{member.discriminator}"
        if member.name != member.display_name:
            member_name = f"{member.display_name} ({member_name})"

        message = self.leave_message.format(member_name=member_name)

        await self.leave_channel.send(message)
