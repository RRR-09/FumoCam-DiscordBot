from asyncio import TimeoutError
from asyncio import sleep as async_sleep
from io import BytesIO
from traceback import format_exc

import nextcord
from nextcord.ext import commands  # type: ignore

from utils import BotClass, log_error, try_delete_message


class Suggestions(commands.Cog):
    def __init__(self, bot: BotClass):
        self.bot = bot

        # Bot channel
        self.suggestions_channel_name = self.bot.CFG.get("suggestions_channel")
        if self.suggestions_channel_name is None:
            print(
                "['suggestions_channel' not specified in config, disabling suggestions subroutine]"
            )
            return
        if self.suggestions_channel_name not in self.bot.channels:
            print(
                f"['{self.suggestions_channel_name}' not found, disabling suggestions subroutine]"
            )
            return
        self.suggestions_channel = self.bot.channels[self.suggestions_channel_name]

        # Human Channel
        self.suggestions_human_channel_name = self.bot.CFG.get(
            "suggestions_human_channel"
        )
        if self.suggestions_human_channel_name is None:
            print(
                "['suggestions_human_channel' not specified in config, disabling suggestions subroutine]"
            )
            return

        if self.suggestions_human_channel_name not in self.bot.channels:
            print(
                f"['{self.suggestions_channel_name}' not found, disabling suggestions subroutine]"
            )
            return
        self.suggestions_human_channel = self.bot.channels[
            self.suggestions_human_channel_name
        ]

        # Other config options
        self.cancel = self.bot.CFG.get("suggestions_cancel", "❌")
        self.confirmation_format = self.bot.CFG.get(
            "suggestions_confirmation_format",
            "Your suggestion has been added.\nYou can undo this by pressing {cancel_emoji} in the next 30 seconds.",
        ).format(cancel_emoji=self.cancel)
        self.deleted_format = self.bot.CFG.get(
            "suggestions_deleted_format", "Your suggestion has been deleted."
        )
        self.downvote = self.bot.CFG.get("suggestions_downvote", "👎")
        self.prefix = self.bot.CFG.get("suggestions_prefix", "--")
        self.suggestion_format = self.bot.CFG.get(
            "suggestions_format",
            "** **\n** **\n__**SUGGESTION FROM {author}:**__\n{suggestion}\n** **\n** **",
        )
        self.upvote = self.bot.CFG.get("suggestions_upvote", "👍")
        self.ready = True

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if not self.ready:
            return
        if message.channel.id != self.suggestions_human_channel.id:
            return
        if not message.content.startswith(self.prefix):
            return

        content = message.clean_content.replace(self.prefix, "", 1)
        author = message.author.mention
        attachments = []
        for attachment in message.attachments:
            try:
                attachment_obj = BytesIO()
                await attachment.save(attachment_obj)
                attachments.append(
                    nextcord.File(attachment_obj, filename=attachment.filename)
                )
            except Exception:
                log_error(format_exc())

        suggestion_text = self.suggestion_format.format(
            author=author, suggestion=content
        )
        suggestion = await self.suggestions_channel.send(
            content=suggestion_text, files=attachments
        )
        await suggestion.add_reaction(self.upvote)
        await suggestion.add_reaction(self.downvote)

        confirmation = await self.suggestions_human_channel.send(
            self.confirmation_format
        )
        await confirmation.add_reaction(self.cancel)

        def cancel_suggestion_react_check(reaction, user):
            return (
                user == message.author
                and str(reaction.emoji) == self.cancel
                and reaction.message.id == confirmation.id
            )

        try:
            await self.bot.client.wait_for(
                "reaction_add", timeout=30.0, check=cancel_suggestion_react_check
            )
        except TimeoutError:
            await try_delete_message(message)
            await try_delete_message(confirmation)
        else:
            await try_delete_message(suggestion)
            await try_delete_message(confirmation)
            deleted_confirmation = await self.suggestions_human_channel.send(
                "Your suggestion has been deleted."
            )
            await async_sleep(5)
            await try_delete_message(deleted_confirmation)
