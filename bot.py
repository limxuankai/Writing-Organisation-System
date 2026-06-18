import os

from dotenv import load_dotenv
from discord.ext import commands
from Setup import sqlquery
from alive import keep_alive
import discord
from discord.utils import get
import json
import asyncio

load_dotenv()


TOKEN = os.getenv("TOKEN")
SERVER_ID =os.getenv("SERVER_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")
REACT_ID = 1470005489491378197
STATUS = "closed"

keep_alive()

# Embed color (optional hex in .env like EMBED_COLOR=#1ABC9C)
EMBED_COLOR_HEX = os.getenv("EMBED_COLOR", "#8a6ed6")

def parse_hex_color(hex_str: str) -> discord.Color:
    try:
        if hex_str.startswith('#'):
            hex_str = hex_str[1:]
        value = int(hex_str, 16)
        return discord.Color(value)
    except Exception:
        return discord.Color.default()

EMBED_COLOR = parse_hex_color(EMBED_COLOR_HEX)

with open("descriptive_roles.json", "r", encoding="utf-8") as f:
    ROLE_MENUS = json.load(f)

class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.tree = discord.app_commands.CommandTree(self)

    async def on_ready(self):
        print(f"✅ Logged in as {self.user} (ID: {self.user.id})")
        try:
            guild = discord.Object(id=SERVER_ID)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)  
            print(f"🔗 Synced {len(synced)} command(s) to guild {SERVER_ID}")
        except Exception as e:
            print(f"❌ Sync error: {e}")


bot = MyBot()

@bot.event
async def on_member_join(member):
    print("Member Joined")
    role = discord.utils.get(member.guild.roles, id=1422461691614068866)
    if role:
        print("Member Added Role")
        await member.add_roles(role)


@bot.tree.command(name="status", description="Check to see if my commissions are open or not!")
async def status(interaction: discord.Interaction):
    await interaction.response.send_message(f"Commissions are {STATUS}, {interaction.user.mention}!")


@bot.tree.command(name="queue", description="Check to see how long my queue is currently!")
async def queue(interaction: discord.Interaction):
    Comms_Info = sqlquery("SELECT * FROM COMMISSION INNER JOIN Clients ON Clients.Name = Commission.Client;")
    Comms_List = [i for i in Comms_Info if i[4] != "On Hold"]
    Within_Queue = len(Comms_List)
    Max_Queue = 6

    if Within_Queue == Max_Queue:
        await interaction.response.send_message(f"Currently maxed out with {Max_Queue} Commission. Commissions currently closed :( {interaction.user.mention} ")
    else:
        await interaction.response.send_message(f"It is currently {Within_Queue}/6 Commissions, {interaction.user.mention}! ")


@bot.tree.command(name="statistic", description="Check your individual statitics!")
async def stats(interaction: discord.Interaction):
    user = str(interaction.user)
    Relevent_Details = sqlquery("SELECT * FROM Clients WHERE name = ?", (user,))
    try:
        Relevent_Details = Relevent_Details[0]
        Name = Relevent_Details[1]
        Number_Of_Words_Commissioned = Relevent_Details[2]
        Patreon_Pledge = Relevent_Details[3]
        Word_Bank = Relevent_Details[4]

        Cost_Per_Thousand_Words = 40
        if Number_Of_Words_Commissioned >= 25: 
            Cost_Per_Thousand_Words = 25
        elif Number_Of_Words_Commissioned >= 15:
                Cost_Per_Thousand_Words = 35
        patron_prices = {
                25: 25,
                20: 30,
                6: 35,
                3: 35,
                0: 50,
                67: 120
            }
        patron_rate = patron_prices[Patreon_Pledge]
        
        Payrate = min(patron_rate, Cost_Per_Thousand_Words)
        
        embed = discord.Embed(
            title="📊 bot Individual Statistics",
            description=f"Here are your current stats, {interaction.user.mention}!",
            color=discord.Color.blurple()
        )


        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        embed.description = (
            f"**Name: {Name}**\n\n"
            f"**Total Words Commissioned: {Number_Of_Words_Commissioned}K Words**\n\n"
            f"**Patron Pledge per Month: ${Patreon_Pledge}** \n\n"
            f"**Current Words in Word Bank: {Word_Bank} Words ** \n\n"
            f"**Current Payrate: ${Payrate} per 1K words** \n\n"
        )
        await interaction.user.send(embed=embed)
        await interaction.response.send_message("✅ I sent your stats in DMs!", ephemeral=True)
    except IndexError:
        await interaction.user.send("User is not found within our database. Please contact xk to fix this issue!")
        await interaction.response.send_message("An error has occured!", ephemeral=True)

@bot.event
async def on_message(message):
    if message.channel.id == REACT_ID:
        if message.content.startswith('roles'):
            keys = ["pronouns", "kinks", "watching", "misc"]
            for i in keys:
                menu = ROLE_MENUS.get(i, {})
                Content = menu.get('description', '')
                emoji_list = []
                for row in menu.get("components", []):
                    for comp in row:
                        label = comp.get('label', 'Unknown Label')
                        emoji = comp.get('emoji', '❓')
                        Content += f"\n{label} {emoji}"
                        emoji_list.append(emoji)

                embedvar = discord.Embed(title=menu.get('title', i),
                                         description=Content,
                                         color=EMBED_COLOR)
                sent = await message.channel.send(embed=embedvar)
                # add reactions for users to click
                for e in emoji_list:
                    try:
                        await sent.add_reaction(e)
                        await asyncio.sleep(0.25)
                    except Exception:
                        print(f"Failed to react {e} to message {sent.id}")
                await asyncio.sleep(0.6)


# Dynamic reaction handlers using descriptive_roles.json and react_messages.json
@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.user_id == bot.user.id:
        return
    if payload.guild_id is None:
        return
    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return

    emoji = str(payload.emoji)
    role = None
    mapping = REACT_MESSAGE_MAP.get(str(payload.message_id)) if 'REACT_MESSAGE_MAP' in globals() else None

    # Prefer stored per-message mapping
    if mapping:
        role_id = mapping.get('emoji_map', {}).get(emoji)
        if role_id:
            role = guild.get_role(int(role_id))
    else:
        # Fallback: search descriptive_roles.json menus for the emoji
        for menu in ROLE_MENUS.values():
            for row in menu.get('components', []):
                for comp in row:
                    if str(comp.get('emoji')) == emoji:
                        role = guild.get_role(int(comp.get('role_id')))
                        menu_exclusive = menu.get('exclusive', False)
                        break
                if role:
                    break
            if role:
                break

    if role is None:
        return

    try:
        member = guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)
        # If mapping indicates exclusive menu, remove other roles from same menu
        if mapping and mapping.get('exclusive'):
            for other_id in mapping.get('emoji_map', {}).values():
                if int(other_id) != int(role.id):
                    other_role = guild.get_role(int(other_id))
                    if other_role and other_role in member.roles:
                        await member.remove_roles(other_role)
        await member.add_roles(role)
        print(f"Assigned {member} to {role}.")
    except Exception as e:
        print(f"Failed to add role: {e}")


@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    if payload.user_id == bot.user.id:
        return
    if payload.guild_id is None:
        return
    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return

    emoji = str(payload.emoji)
    role = None
    mapping = REACT_MESSAGE_MAP.get(str(payload.message_id)) if 'REACT_MESSAGE_MAP' in globals() else None

    if mapping:
        role_id = mapping.get('emoji_map', {}).get(emoji)
        if role_id:
            role = guild.get_role(int(role_id))
    else:
        for menu in ROLE_MENUS.values():
            for row in menu.get('components', []):
                for comp in row:
                    if str(comp.get('emoji')) == emoji:
                        role = guild.get_role(int(comp.get('role_id')))
                        break
                if role:
                    break
            if role:
                break

    if role is None:
        return

    try:
        member = guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)
        if role in member.roles:
            await member.remove_roles(role)
            print(f"Removed {role} from {member}.")
    except Exception as e:
        print(f"Failed to remove role: {e}")

bot.run(TOKEN)
