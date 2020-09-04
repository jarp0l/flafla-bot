#!/usr/bin/env python3
#top
import discord # For discord
from discord.ext import commands # For commands
from pathlib import Path # For paths
from datetime import datetime # For date and time
from random import choice
import json, logging, asyncpg, pytz, traceback

NPT = pytz.timezone('Asia/Kathmandu')
#NPT holds the date and time data according to time zone of Asia/Kathmandu
#this will be used while inserting anything to the database

#cwd = current working directory, to get the current directory to navigate through the files
cwd = Path(__file__).parents[0]
cwd = str(cwd)
# print(f"{cwd}\n-----")

#Defining a few things
secret_file = json.load(open(cwd+'/bot_config/secrets.json'))
bot = commands.Bot(command_prefix='-', case_insensitive=True, owner_ids=secret_file['OWNER_IDS'])
bot.config_token = secret_file['token']
logging.basicConfig(level=logging.INFO) #shows logging info on the console

DB_URI = secret_file['1']   #1 means active, 0 means inactive; go to secrets.json to change the mode

#some other constants used throughout the code:
MOD_CHANNEL = secret_file['MOD_CHANNEL']
ADD_PUBLISH_CHALLENGE_CHANNEL = secret_file['ADD_PUBLISH_CHALLENGE_CHANNEL']
CHALLENGE_UPDATES_CHANNEL = secret_file['CHALLENGE_UPDATES_CHANNEL']
CHALLENGE_PUBLISH_CHANNEL = secret_file['CHALLENGE_PUBLISH_CHANNEL']

bot.color_list = [0x45CE30, 0xFFF222, 0x7B8788, 0x8B78E6, 0x3498DB, 0x5005EF, 0xF81F90]
# colors_test = [#45CE30, #FFF222, #7B8788, #8B78E6, #3498D8, #5005EF, #F81F90]
#to generate and use a random color just use choice(bot.color_list)


#flag encryption code
import hashlib
#begin---
def encrypt(flag):
    md = hashlib.md5(flag.encode('ascii'))
    salted = md.hexdigest() + flag
    encrypted = hashlib.sha256(salted.encode('ascii'))
    return encrypted.hexdigest().split('\n')[0]
#end of encrypt function---

#whenever the bot is ready/online this will be triggered
#on_ready
@bot.event
async def on_ready():
    print(f"-----\nLogged in as: {bot.user.name} : {bot.user.id}\n-----\nMy current prefix is: -\n-----")

    await bot.change_presence(activity=discord.Game(name=f"Hi, I am {bot.user.name}.\nUse prefix `-` to interact with me. For example: `-help`.")) # This changes the bot's 'activity' that is see on profile pop-up

#on_member_join
@bot.event 
async def on_member_join(member):

    embed = discord.Embed(title="Welcome!!!", description=f'''
    Hey {member.name.mention}, we all would like to warmly welcome you to our server: **{member.guild}**\n
    Some channels to visit in this server:
     \\***#welcome:** *know the reason behind creating this server*
     \\***#rules: ** *rules you **must** follow everywhere on this server*
     \\*and all the other channels actually :smile:

    Please remember that you will not be able to add challenges and submit flags for our CTF challenges until you send a message with your 'rollnumber and nickname' to our bot 'Flafla'. 
    This is the format you should follow: `-accept <rollnum_nickname>`. 
    For example: 
    `-accept 076BEI049_nickname` 
    (you shouldn't format the message this way though, just send a plain message)
    \nNOTE: THIS COMMAND WORKS ONLY ON **#new-arrivals** CHANNEL. So, do it there.

    For other help commands, just send our bot the command: `-help` 

    FROM:
        ''', color=choice(bot.color_list))

    # embed.set_thumbnail(url=ctx.author.avatar_url)
    embed.set_author(name=member.name, icon_url=member.avatar_url)
    embed.set_footer(text=member.guild, icon_url=member.guild.icon_url)

    await member.create_dm()
    await member.dm_channel.send(embed=embed)



#commands:
#hi
@bot.command(name='hi', aliases=['hello'])      #works with 'hi' as well as 'hello'
async def _hi(ctx):
    """
    A simple command which says hi back to the author.
    """
    await ctx.send(f"Hi {ctx.author.mention}!")


    
#logout/#close
@bot.command(aliases=['disconnect', 'close', 'stop'])
@commands.is_owner()
async def logout(ctx):
    """
    If the user running the command owns the bot then this will disconnect the bot from discord. For development purpose only.
    """
    await ctx.send(f"Hey {ctx.author.mention}, I am now logging out :wave:")
    await bot.logout()

# @logout.error
# async def logout_error(ctx, error):
#     """
#     Whenever the logout command has an error this will be tripped.
#     """
#     if isinstance(error, commands.CheckFailure):
#         await ctx.send("Hey! You lack permission to use this command as you do not own the bot.")
#     # else:
    #     raise error


#echo
@bot.command()
async def echo(ctx, *, message=None):
    """
    A simple command that repeats the author's input back to them.
    """
    message = message or "Please provide the message to be repeated."
    
    await ctx.send(message)






#add
@bot.group(name='add', case_insensitive=True, invoke_without_command=True)
async def add(ctx):
    """
    Use this to add challenge or flag.
    """
    # if ctx.channel.id != ADD_PUBLISH_CHALLENGE_CHANNEL:    #id of bot-test channel in CTF
    #     return

    await ctx.channel.send("Challenge or Flag? Please follow the correct syntax. Type `-help add` for help.")


#add_challenge
#challenge
@add.command(name='challenge', aliases=['chal'])
async def add_challenge(ctx, category, *, description):
    if ctx.channel.id != ADD_PUBLISH_CHALLENGE_CHANNEL:    #id of bot-test channel in CTF
        return
    # try:
    conn = await asyncpg.connect(DB_URI)

    await conn.execute('''
        INSERT INTO challenges (
            author_id,
            added_on,
            category, 
            challenge_description,
            messsage_id
        ) 
        VALUES ($1, $2, $3, $4, $5)
        ''',
            ctx.author.id, 
            datetime.now(NPT).replace(microsecond=0, tzinfo=None), 
            category,
            description,
            ctx.message.id
        )
    
    chal_id = await conn.fetchval('''
        SELECT challenge_id 
            FROM challenges 
                WHERE challenge_id = (SELECT MAX(challenge_id) FROM challenges)
    ''')    #MAX() function is used so that the id with the highest or max value is returned, i.e. the latest added challenge

    await conn.close()
    await ctx.channel.send(f"{ctx.author.mention} Your challenge was added as id: {chal_id}. Send publish command with this id when you are ready to publish it!")
    # await ctx.channel.send(f"category: {category}\n\ndescription: {description}\n\nauthor: {ctx.author}\n\nYour challenge has been added!")

    # except Exception as e:
    #     channel = bot.get_channel(MOD_CHANNEL)
    #     await channel.send(f"error on command `-add challenge`: {e}")



# @add_challenge.error
# async def add_challenge_error(ctx, error):
#     """
#     Whenever the command has an error this will be tripped.
#     """
#     if isinstance(ctx, commands.MissingRequiredArgument):
#         await ctx.send("You did not specify enough number of arguments. Type `-help add challenge` for help.")
    
#     if isinstance(error, commands.CommandInvokeError):
#         await ctx.send("Seems like you are not registered yet.")

#     else:
#         raise error






#add_flag
#flag
@add.command(name='flag')
@commands.dm_only()
async def add_flag(ctx, challenge_id, flag):
    '''
    Use this to add flag to the challenge added using -add challenge.
    '''
    # try:
    challenge_id = int(challenge_id)

    conn = await asyncpg.connect(DB_URI)

    data = await conn.fetchval('''
        SELECT author_id 
            FROM challenges 
                WHERE challenge_id = $1
    ''', challenge_id)

    if int(data) == int(ctx.author.id):
        encrypted_flag = encrypt(flag)
        await conn.execute('''
            INSERT INTO flags(
                challenge_id, 
                added_on,
                flag,
                message_id
            )
            VALUES($1, $2, $3, $4)
            ''',
                challenge_id, 
                datetime.now(NPT).replace(microsecond=0, tzinfo=None),
                encrypted_flag,
                ctx.message.id
            )

        await conn.close()

        await ctx.channel.send(f"Congrats! Your flag has been added!")

    elif data is None:
        await ctx.channel.send("There is no challenge with that id.")

    else:
        await ctx.channel.send("You didn't add the challenge, so you can't add the flag as well.")

    # except Exception as e:
    #     # await ctx.channel.send("Please follow the correct syntax.")
    #     channel = bot.get_channel(MOD_CHANNEL)
    #     await channel.send(f"error on command `-add flag`: {e}")




# @add_flag.error
# async def add_flag_error(ctx, error):
#     """
#     Whenever the command has an error this will be tripped.
#     """
#     if isinstance(error, commands.MissingRequiredArgument):
#         await ctx.send("You did not specify all the arguments. Type `-help add flag` for help.")
    
#     elif isinstance(error, commands.CommandInvokeError):
#         await ctx.send("Did you check your syntax properly? Type `-help add flag` for help.")
    
#     elif isinstance(error, commands.PrivateMessageOnly):
#         await ctx.message.delete()
#         await ctx.send("Your recent message has been deleted. You can use this command only in DM.")
    
#     else:
#         raise error





#--------------------------------------------------------------

#submit
@bot.command(name='flag', aliases=['submit', 'submit-flag'], invoke_without_command=True)
@commands.dm_only()
@commands.cooldown(rate=1, per=60, type=commands.BucketType.user)
async def submit_flag(ctx, challenge_id, flag):
    '''
    Submit the flag you captured!
    '''
    # try:  
    challenge_id = int(challenge_id)

    conn = await asyncpg.connect(DB_URI)

    data = await conn.fetchval('''
        SELECT flag 
            FROM flags 
                WHERE challenge_id = $1
    ''', challenge_id)

    #cache to be introduced instead of accessing the db everytime a flag is submitted
    # cache = get() #was trying to use a dictionary here
    #but the documentation of asyncpg states that fetchval, fetchrow already implement
    #caching mechanism, lru_cache mechanism to be exact

    encrypted_flag = encrypt(flag)

    if data is None:
        await ctx.channel.send("There is no challenge with that id.")

    elif str(data) == encrypted_flag:  #place here hashing/encryption

        await conn.execute('''
            INSERT INTO solvers (
                challenge_id, 
                member_id, 
                solved_on, 
                message_id_on_success
            )
            VALUES ($1, $2, $3, $4)
            ''',
                challenge_id, 
                ctx.author.id, 
                datetime.now(NPT).replace(microsecond=0, tzinfo=None),
                ctx.message.id
            )

        await conn.close()

        await ctx.channel.send(f"Wow! Your flag is correct!")
        
        channel = bot.get_channel(CHALLENGE_UPDATES_CHANNEL) #to send the below message to this channel
        await channel.send(f"Hey @everyone, {ctx.author.mention} just solved the challenge with id: {challenge_id}!")

    else:
        await ctx.channel.send("That was incorrect. Do try again.")

        await conn.execute('''
            INSERT INTO submissions (
                challenge_id,
                member_id,
                submitted_flags,
                added_on,
                message_id
            )
            VALUES ($1, $2, $3, $4, $5)
            ''',
                challenge_id,
                ctx.author.id,
                flag,
                datetime.now(NPT).replace(microsecond=0, tzinfo=None),
                ctx.message.id
            )

        await conn.close()


    # except Exception as e:
    #     # await ctx.channel.send("Please follow the correct syntax.")
    #     await ctx.channel.send(e)






# @submit_flag.error
# async def submit_flag_error(ctx, error):
#     """
#     Whenever the command has an error this will be tripped.
#     """
#     if isinstance(error, commands.MissingRequiredArgument):
#         await ctx.send("You did not specify all the arguments. Type `-help submit` for help.")
    
#     elif isinstance(error, commands.PrivateMessageOnly):
#         await ctx.message.delete()
#         await ctx.send("Ssshh! Not here..DM me. :smiley:")
    
#     else:
#         raise error








#publish
@bot.command(name='publish')
async def publish_chal(ctx, challenge_id):
    '''
    Publish the challenge after adding one.
    '''
    if ctx.channel.id != ADD_PUBLISH_CHALLENGE_CHANNEL:    #id of bot-test channel in CTF
        return
    
    # else:
    try:
        chal_id = int(challenge_id)

        conn = await asyncpg.connect(DB_URI)

        data = await conn.fetchrow('''
            SELECT author_id, category, challenge_description 
                FROM challenges 
                    WHERE challenge_id = $1
        ''', chal_id)

        await conn.close()

        if data is None:
            await ctx.channel.send("The challenge with that id doesn't exist.")

        elif int(data['author_id']) != int(ctx.author.id):
            await ctx.channel.send("Why are you trying to publish someone else's challenge?")

        else:
            channel = bot.get_channel(CHALLENGE_PUBLISH_CHANNEL) #to publicly post the challenge
     
            embed = discord.Embed(title="New challenge published!", description=f"{ctx.author.mention} just published the following challenge:", color=choice(bot.color_list))
            embed.add_field(name="CHALLENGE ID:", value=f"{chal_id}")
            # embed.add_field(name="ADDED ON:", value=f"{data['date_added']}")
            embed.add_field(name="CATEGORY:", value=f"{data['category']}")
            embed.add_field(name="DESCRIPTION:", value=f"{data['challenge_description']}", inline=False)
            await channel.send("@everyone")
            await channel.send(embed=embed)

            await ctx.channel.send("Wohoo! Your challenge is now published!")

    except ValueError:
        await ctx.send("You should send me the challenge id to publish.")
        # raise error
        # await ctx.channel.send("You didn't provide the challenge number to publish")



# @publish_chal.error
# async def publish_errors(ctx, error):
#     """
#     Whenever the command has an error this will be tripped.
#     """
#     if isinstance(error, commands.MissingRequiredArgument):
#         await ctx.send("You did not specify enough number of arguments. Type `-help publish` for help.")
#     else:
#         raise error








#moderation
#agree
@bot.command(name='agree')
async def agreement(ctx, rollnum_nickname):
    """
    For new-comers to the server. After giving rollnum_nick, the role 'members' will be given and the nickname will be changed to the given form.
    """
    # role_id = secret_file['MEMBER_ROLE_ID'] #'members' role
    # role = ctx.guild.get_role(role_id)
    # await ctx.author.add_roles(role, reason="Agreed to the rules")
    await ctx.author.edit(nick=rollnum_nickname)
    
    conn = await asyncpg.connect(DB_URI)
    
    await conn.execute('''
        INSERT INTO members (
            member_id,
            server_nickname,
            added_on,
            message_id
        )
        VALUES ( $1. $2 , $3, $4)
        ''',
            ctx.author.id,
            rollnum_nickname, 
            datetime.now(NPT).replace(microsecond=0, tzinfo=None)
        )
    await conn.close()
    # await ctx.channel.send(f"Hey {ctx.author.mention}, you now have been given the role {role.mention}, and take a look at your nickname, it has been changed to __**{rollnum_nickname}**__ in this server!")
    await ctx.channel.send(f"Congratulations {ctx.author.mention}, you have been added to the database and your nickname has been changed! Now you can add challenges as well as submit flags!")



# @agreement.error
# async def agreement_errors(ctx, error):
#     """
#     Whenever the command has an error this will be tripped.
#     """
#     # if isinstance(error, commands.MissingRequiredArgument):
#     #     await ctx.send("You did not specify enough number of arguments. Type `-help agree` for help.")
    
#     if isinstance(error, commands.CommandInvokeError):
#         await ctx.send("Seems like you are already registered.")

#     # else:
    #     raise error



#register
@bot.command()
async def register(ctx, rollnum_nickname):
    """
    For the members already on the server. This just gives the role but does not change the nickname.
    """
    # role_id = 749550229115895840 #'members' role
    # role = ctx.guild.get_role(role_id)
    # await ctx.author.add_roles(role, reason="Added to db")

    conn = await asyncpg.connect(DB_URI)
    
    await conn.execute('''
        INSERT INTO members (
            member_id,
            server_nickname,
            added_on,
            message_id
        )
        VALUES ($1, $2, $3, $4)
        ''', 
            ctx.author.id, 
            rollnum_nickname,
            datetime.now(NPT).replace(microsecond=0, tzinfo=None),
            ctx.message.id
        )

    await conn.close()

    # await ctx.channel.send(f"Hey {ctx.author.mention}, you now have been given the role {role.mention}.")
    await ctx.channel.send(f"Congratulations {ctx.author.mention}, you have been added to the database! Now you can add challenges as well as submit flags!")



# @register.error
# async def register_errors(ctx, error):
#     """
#     Whenever the command has an error this will be tripped.
#     """
#     if isinstance(error, commands.CommandInvokeError):
#         await ctx.send("Seems like you are already registered.")

    # else:
    #     raise error






#extra
#execute
@bot.command(aliases=['exec', 'exc'])
@commands.is_owner()
async def execute(ctx, *, query):
    """
    Execute the query. Only for debugging purpose.
    """
    if ctx.channel.id != MOD_CHANNEL:
        return

    conn = await asyncpg.connect(DB_URI)
    
    result = await conn.fetch(query)

    await conn.close()

    channel = bot.get_channel(MOD_CHANNEL)
    await channel.send(f"{result}")




#global error handler
@bot.event
async def on_command_error(ctx, error):
    """The event triggered when an error is raised while invoking a command.

    Parameters
    ------------
    ctx: commands.Context
        The context used for command invocation.
    error: commands.CommandError
        The Exception raised.
    """
    #Ignore these errors
    ignored = (commands.CommandNotFound, commands.UserInputError)
    if isinstance(error, ignored):
        return
    
    # This prevents any commands with local handlers being handled here in on_command_error.
    elif hasattr(ctx.command, 'on_error'):
        return

    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"One or more argument is missing. Please check and try again. Or type `-help {ctx.command}` for help.")
    
    elif isinstance(error, commands.PrivateMessageOnly):
            await ctx.message.delete()
            await ctx.send("Ssshh! Not here..DM me. :smiley:")

    elif isinstance(error, commands.CheckFailure):
        await ctx.send("Hey! You lack permission to use that command!")
    
    # elif isinstance(error, commands.CommandOnCooldown):
    #     # If the command is currently on cooldown trip this
    #     m, s = divmod(error.retry_after, 60)
    #     h, m = divmod(m, 60)
    #     if int(h) is 0 and int(m) is 0:
    #         await ctx.send(f' You must wait {int(s)} seconds to use this command!')
    #     elif int(h) is 0 and int(m) is not 0:
    #         await ctx.send(f' You must wait {int(m)} minutes and {int(s)} seconds to use this command!')
    #     else:
    #         await ctx.send(f' You must wait {int(h)} hours, {int(m)} minutes and {int(s)} seconds to use this command!')
   
    elif isinstance(error, commands.CommandInvokeError):
        await ctx.send("Something does not seem right. Type `-help` if you need any help.")
        channel = bot.get_channel(MOD_CHANNEL) #to send the below message to this channel
        await channel.send(f"Error encountered by {ctx.author.name}, {ctx.author.id}\nEncountered error: \n{error}")
    
    else:
        # All other Errors not returned come here. And we can just print the default TraceBack.
        # print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        # traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

        channel = bot.get_channel(MOD_CHANNEL)
        await channel.send(f"Error encountered by: {ctx.author.name}, {ctx.author.id}\nError encountered in: {ctx.command}\n{error}")







#----------------------------------------------------------------------------

bot.run(bot.config_token) # Runs our bot


'''
FOOTNOTES:
https://discordpy.readthedocs.io/en/latest/ext/commands/commands.html#invocation-context
 => for context.guild, context.author matters


https://discordpy.readthedocs.io/en/latest/ext/commands/api.html
 => discord.py's command extension module (discord.ext.commands)

'''
#END