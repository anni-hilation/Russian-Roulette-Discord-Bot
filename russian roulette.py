import os
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
from datetime import timedelta

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
guild_players = {}
game_difficulty = {}
game_owner = {}


duration = timedelta(minutes=5)

TOKEN = "YOUR_TOKEN_HERE"

HELP_TEXT = """
**🎲 Russian Roulette Bot Help**

**Commands:**
/russian_roulette - Start a game. Users can type "Me!" to join and "Done." to finish player selection.
/help - Get help.
/check_roles - Check if bots role is high enough to reliably mute/kick/ban members.

**Game Rules:**
- Minimum 2 players, maximum 10 players per game.
- Only the person who started the game can type "Done."
- The bot will randomly select a loser.

**Punishments:**
- Easy: 5-minute mute
- Medium: Kick
- Hard: Ban

⚠️ The bot cannot mute, kick or ban the server owner.
"""

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")


@bot.tree.command(name="russian_roulette", description="Russian roulette, loser gets muted/kicked/banned.")
@app_commands.choices(
    difficulty=[
        app_commands.Choice(name="Easy - 5 minute mute", value="1"),
        app_commands.Choice(name="Medium - Kick", value="2"),
        app_commands.Choice(name="Hard - Ban", value="3"),
    ]
)
async def russian_roulette(interaction: discord.Interaction, difficulty: app_commands.Choice[str]):
    guild_id = interaction.guild.id
    guild_players[guild_id] = []
    game_owner[guild_id] = interaction.user
    game_difficulty[guild_id] = difficulty.value


    await interaction.response.send_message(
        'Type "Me!" in chat to join. Type "Done." when all players are ready.', ephemeral=False
    )


@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    guild_id = message.guild.id
    if guild_id not in guild_players:
        return  # no game started

    players = guild_players[guild_id]
    content = message.content.lower()

    # Join player
    if "me!" in content:
        
        if message.author == message.guild.owner:
            await message.channel.send(f"Sorry {message.author.display_name}, the server owner cannot join!")
            return
        
        elif message.author not in players:
            players.append(message.author)
            await message.channel.send(f"{message.author.display_name} joined the game!")
        else:
            await message.channel.send(f"{message.author.display_name} is already in the game!")

    elif "done." in content:
        if message.author != game_owner.get(guild_id):
            await message.channel.send(f"❌ Only {game_owner[guild_id].display_name}, the person who started the game, can type 'Done.'")
            return
        elif len(players) > 10:
            await message.channel.send("Maximum 10 players allowed. Game canceled.")
            guild_players[guild_id].clear()
            return
        else:
            await message.channel.send(
                f"Players ready: {', '.join(p.display_name for p in players)}"
            )

            loser = random.choice(players)
            await message.channel.send(f"💥 {loser.mention} lost!")

            difficulty = game_difficulty.get(guild_id, "1")

            # Apply punishment
            if difficulty == "1":
                await message.channel.send(f"{loser.mention} will be muted for 5 minutes!")
                await asyncio.sleep(2)
                await loser.timeout(duration, reason="Russian roulette loss (Easy)")
            elif difficulty == "2":
                await message.channel.send(f"{loser.mention} will be kicked!")
                await asyncio.sleep(2)
                await loser.kick(reason="Russian roulette loss (Medium)")
            else:
                await message.channel.send(f"{loser.mention} will be banned!")
                await asyncio.sleep(2)
                await loser.ban(reason="Russian roulette loss (Hard)", delete_message_days=0)

            guild_players[guild_id].clear()
            game_owner.pop(guild_id, None)
            game_difficulty.pop(guild_id, None)

    await bot.process_commands(message)

@bot.tree.command(name="check_roles", description="Check if bots role is high enough to kick/ban/mute players")
async def check_roles(interaction: discord.Interaction):
    bot_member = interaction.guild.me 
    highest_role = bot_member.top_role 

    if highest_role.position < len(interaction.guild.roles) - 1:
        await interaction.response.send_message(
            f"⚠️ The bots role '{highest_role.name}' is not at the top of all the server roles. "
            f"Please move it above the players (roles) that the bot should be able to kick/ban/mute. Its impossible to act on the server owner."
        )
    else:
        await interaction.response.send_message("✅ The role is high enough to act on members!")


bot.run(TOKEN)
