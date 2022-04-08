from asyncio import sleep as async_sleep

import nextcord
from discord import VoiceState  # noqa: F401
from nextcord.ext import commands, tasks  # type: ignore

from utils import BotClass


class VoiceChannelHoist(commands.Cog):
    def __init__(self, bot: BotClass):
        self.ready = False
        self.bot = bot
        # Category for voice chats
        voice_channels_category_id = self.bot.CFG.get("voice_channels_category_id")
        voice_channels_category = self.bot.guild.get_channel(voice_channels_category_id)
        if not isinstance(voice_channels_category, nextcord.CategoryChannel):
            print(
                f"[Could not find VC category by id '{voice_channels_category_id}', disabling voice channel hoist "
                "subroutine]"
            )
            return
        self.voice_channels_category: nextcord.CategoryChannel = voice_channels_category

        # Indicator for voice chat user count
        voice_chat_indicator_id = self.bot.CFG.get("voice_chat_indicator_id")
        voice_chat_indicator = self.bot.guild.get_channel(voice_chat_indicator_id)
        if not isinstance(voice_chat_indicator, nextcord.VoiceChannel):
            print(
                f"[Could not find indicator VC channel by id '{voice_chat_indicator_id}', disabling voice channel "
                "hoist subroutine]"
            )
            return
        self.voice_chat_indicator: nextcord.VoiceChannel = voice_chat_indicator

        # Category for indicators
        voice_chat_indictor_category_id = self.bot.CFG.get(
            "voice_chat_indictor_category_id"
        )
        voice_chat_indictor_category = self.bot.guild.get_channel(
            voice_chat_indictor_category_id
        )
        if not isinstance(voice_chat_indictor_category, nextcord.CategoryChannel):
            print(
                f"[Could not find indicator category by id '{voice_chat_indictor_category_id}', disabling voice "
                "channel hoist subroutine]"
            )
            return
        self.voice_chat_indictor_category: nextcord.CategoryChannel = (
            voice_chat_indictor_category
        )

        self.active_position = self.bot.CFG.get("voice_channels_active_pos", 2)
        self.inactive_position = self.bot.CFG.get("voice_channels_inactive_pos", 4)
        self.indicator_format = self.bot.CFG.get(
            "voice_chat_indicator_format", "❗🗣 VC Users: {vc_user_count}"
        )
        self.lowest_position = 0
        for channel in self.bot.guild.channels:
            if channel.position > self.lowest_position:
                self.lowest_position = channel.position

        self.safety_verification_loop.start()
        self.ready = True

    async def update_voice_chat_indicators(self):
        """
        Based on whether there are users in a voice channel or not,
        - Move the VCs category up (visible without scrolling) or down (need to scroll to see) on the list.
        - Move/change visibility for "Users in VC" indicators category to visible+top or invisible+bottom
        - Update indicator on activity to reflect member count
        """

        position = self.voice_channels_category.position
        indicator_position = self.voice_chat_indictor_category.position
        vc_users = 0
        for voice_channel in self.voice_channels_category.voice_channels:
            vc_users += len(voice_channel.members)

        indicator_name = self.indicator_format.format(vc_user_count=vc_users)

        if vc_users > 0:
            if indicator_position != 0:
                # Move indicators to top
                await self.voice_chat_indictor_category.edit(position=0)
                # Make indicators invisible to users
                await self.voice_chat_indictor_category.set_permissions(
                    self.bot.guild.default_role, view_channel=True
                )

            if position != self.active_position:
                # Move category
                await self.voice_channels_category.edit(position=self.active_position)

        elif vc_users <= 0:
            if indicator_position != self.lowest_position:
                # Make indicators invisible to users
                await self.voice_chat_indictor_category.set_permissions(
                    self.bot.guild.default_role, view_channel=False
                )
                # Move indicators to bottom, for admins who can see invisible channels
                await self.voice_chat_indictor_category.edit(
                    position=self.lowest_position
                )

            if position != self.inactive_position:
                # Move category
                await self.voice_channels_category.edit(position=self.inactive_position)

        # Edit indicator to reflect users in VC
        if self.voice_chat_indicator.name != indicator_name:
            await self.voice_chat_indicator.edit(name=indicator_name)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: nextcord.Member,
        before: nextcord.VoiceState,
        after: nextcord.VoiceState,
    ):
        if not self.ready:
            return
        # Let discord process the event so we have ensured correct data next
        await async_sleep(1)
        await self.update_voice_chat_indicators()

    @tasks.loop(seconds=120)
    async def safety_verification_loop(self):
        """
        Because discord silently rate limits, requeue the update every 60s.
        """
        await self.update_voice_chat_indicators()
