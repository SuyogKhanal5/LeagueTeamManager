import discord
from TourneyClasses import Team, Tournament, Match, Player
import random
import numpy as np

class helpers():
    def __init__(self, cursor, db) -> None:
        self.cursor = cursor
        self.db = db

    # SQL get template function
    def get(self, guild_id, column):
        self.cursor.execute("SELECT " + column +
                    " FROM servers WHERE guildId=?", (guild_id,))
        return self.cursor.fetchone()[0]


    # SQL update template function
    def update(self, guild_id, column, value):
        self.cursor.execute("UPDATE servers SET " + column +
                    "=? WHERE guildId=?", (value, guild_id))
        self.db.commit()


    # move players into their corresponding team channels
    async def movefunc(self, ctx):
        channel1name = self.get(ctx.guild.id, "channel1")
        channel2name = self.get(ctx.guild.id, "channel2")
        team1 = self.get(ctx.guild.id, "team1")
        team2 = self.get(ctx.guild.id, "team2")
        new_og = str(ctx.user.voice.channel)

        self.update(ctx.guild.id, "original_channel", new_og)

        team1Obj = Team()
        team1Obj.set_id(1)
        team1Obj.deserializeTeam(team1)
        team2Obj = Team()
        team2Obj.set_id(2)
        team2Obj.deserializeTeam(team2)

        channel1 = discord.utils.get(ctx.guild.channels, name=channel1name)
        channel2 = discord.utils.get(ctx.guild.channels, name=channel2name)

        if channel1 is not None and channel2 is not None:
            for player in team1Obj.players:
                member = discord.utils.get(ctx.guild.members, id=player.id)
                await member.move_to(channel1)

            for player in team2Obj.players:
                member = discord.utils.get(ctx.guild.members, id=player.id)
                await member.move_to(channel2)
        else:
            await ctx.response.send_message('Team Channels Not Set! Use "/set-teams" to set teams.')


    # TODO: what if there are more players in the channel than team sizes?
    # or if number of members if odd?
    async def randomizeTeamHelper(self, ctx):
        await self.clearTeamsHelper(ctx)

        members = []
        team1 = Team()
        team2 = Team()

        channel = ctx.user.voice.channel

        for i in channel.members:
            members.append(i)

        m = np.array(members)
        np.random.shuffle(m)

        for i in range(len(members)):
            newPlayer = Player()
            newPlayer.name = m[i].name
            newPlayer.id = m[i].id

            if i < len(members) / 2:
                team1.add_player(newPlayer)
            else:
                team2.add_player(newPlayer)

        # seriialize both team objs

        serialzedTeam1 = team1.serializeTeam()
        serialzedTeam2 = team2.serializeTeam()

        self.update(ctx.guild.id, "team1", serialzedTeam1)
        self.update(ctx.guild.id, "team2", serialzedTeam2)


    # TODO: Identify captain
    def makeEmbedString(self, team : Team, roles = False):
        teamString = ""
        
        if roles and len(team.players) == 5:
            for i in range(5):
                teamString += roles.get(i) + team.players[i].name + "\n"
        else:
            for player in team.players:
                teamString += player.name + "\n"

        return teamString

    # prints teams in discord channel
    # DO NOT PASS NULL TEAMS
    async def printEmbed(self, ctx, team1 : Team, team2 : Team, playersTeam = None):
        team1_embedString = self.makeEmbedString(team1)
        team2_embedString = self.makeEmbedString(team2)

        team1_embed = discord.Embed(
            title=team1.get_name(), description=team1_embedString, color=discord.Color.blue()
        )
        team2_embed = discord.Embed(
            title=team2.get_name(), description=team2_embedString, color=discord.Color.red()
        )

        await ctx.response.send_message(embed=team1_embed)
        await ctx.channel.send(embed=team2_embed)

        if playersTeam != None:
            playerString = self.makeEmbedString(playersTeam)
            player_embed = discord.Embed(
                title="PLAYERS", description=playerString, color=discord.Color.purple()
            )
            
            await ctx.channel.send(embed=player_embed)

    # sets channels for teams
    # TODO: change teams to expect array of two team names
    async def setTeamHelper(self, ctx, team1 = "Team 1", team2 = "Team 2"):
        guild = ctx.guild

        channel1 = discord.utils.get(ctx.guild.channels, name=team1)

        if channel1 is None:
            await guild.create_voice_channel(name=team1)
            channel1 = discord.utils.get(ctx.guild.channels, name=team1)

        channel2 = discord.utils.get(ctx.guild.channels, name=team2)

        if channel2 is None:
            await guild.create_voice_channel(name=team2)
            channel2 = discord.utils.get(ctx.guild.channels, name=team2)

        self.update(guild.id, "channel1", str(team1))
        self.update(guild.id, "channel2", str(team2))

        await ctx.response.send_message("Channels set!")

    # TODO: rename this wtf
    # randomizes teams and player roles


    async def both(self, ctx):
        await self.randomizeTeamHelper(ctx)
        await self.randomRoleHelper(ctx)


    async def randomRoleHelper(self, ctx):
        global roles

        result1 = ""
        result2 = ""

        team1 = self.get(ctx.guild.id, "team1")
        team2 = self.get(ctx.guild.id, "team2")

        random.shuffle(team1)
        random.shuffle(team2)

        # TODO: currently hardcoded but should add a way to create team of any size
        # e.g. based on game, different hashmaps for role
        for i in range(10):
            if i < 5:
                result1 += roles.get(i % 5) + str(team1[i % 5]) + "\n"
            else:
                result2 += roles.get(i % 5) + str(team2[i % 5]) + "\n"

        self.update(ctx.guild.id, "result1", result1)
        self.update(ctx.guild.id, "result2", result2)


    # chooses captains for each team at random
    async def captainsHelper(self, ctx, captain_1, captain_2):
        await self.clearTeamsHelper(ctx)

        # TODO: remove result1, result2, using_captains_ and original_channel
        result1 = ""
        result2 = ""
        team1ids = []
        team2ids = []
        team1 = []
        team2 = []

        self.update(ctx.guild.id, "captain1", captain_1.id)
        self.update(ctx.guild.id, "captain2", captain_2.id)
        self.update(ctx.guild.id, "using_captains", True)
        self.update(ctx.guild.id, "original_channel",
            str(ctx.message.author.voice.channel))
        original_channel = self.get(ctx.guild.id, "original_channel")

        if captain_1 is None or captain_2 is None:
            await ctx.response.send_message("Mention two team captains!")
        elif captain_1 == captain_2:
            await ctx.response.send_message("Mention two different people!")
        else:
            # TODO: why do we use captain_1? seems useless asf
            captain1 = captain_1
            result1 += str(captain1.name)
            self.update(ctx.guild.id, "result1", result1)
            team1ids.append(captain1.id)
            self.update(ctx.guild.id, "team1ids", team1ids)
            team1.append(captain1.name)
            self.update(ctx.guild.id, "team1", team1)

            captain2 = captain_2
            result2 += str(captain2.name)
            self.update(ctx.guild.id, "result2", result2)
            team2ids.append(captain2.id)
            self.update(ctx.guild.id, "team2ids", team2ids)
            team2.append(captain2.name)
            self.update(ctx.guild.id, "team2", team2)

            await self.printEmbed(
                ctx, discord.utils.get(ctx.guild.channels, name=original_channel)
            )

            await ctx.response.send_message("Captains selected!")
            await ctx.response.send_message(
                captain_1.mention
                + ', type ".choose  @_____" to pick a player for your team'
            )


    # function for captain to choose a specific team member
    async def chooseFunc(self, ctx, member):
        # TODO: remove drafted, captainsNum
        drafted = self.get(ctx.guild.id, "drafted")
        team_size = self.get(ctx.guild.id, "team_size")
        captainNum = self.get(ctx.guild.id, "captainNum")
        captain1id = self.get(ctx.guild.id, "captain1")
        captain2id = self.get(ctx.guild.id, "captain2")

        captain1 = discord.utils.get(ctx.guild.members, id=captain1id)
        captain2 = discord.utils.get(ctx.guild.members, id=captain2id)

        # TODO: clean this up. maybe use guard clauses instead?
        if drafted < (team_size * 2):
            if captainNum == 1 and ctx.message.author.id == captain1.id:
                await self.chooseHelper(ctx, member, 1)
            elif captainNum == 2 and ctx.message.author.id == captain2.id:
                await self.chooseHelper(ctx, member, 2)
            else:
                if (captainNum == 1 and ctx.message.author.id == captain2.id) or (
                    captainNum == 2 and ctx.message.author.id == captain1.id
                ):
                    await ctx.response.send_message("Not Your Turn!")
                elif (
                    ctx.message.author.id != captain1.id
                    and ctx.message.author.id != captain2.id
                ):
                    await ctx.response.send_message("Only team captains can use this command!")


    # choose random player from all remaining players
    async def chooseRandomMember(self, ctx):
        randomMember = await self.getRandomMember(ctx)
        await self.chooseFunc(ctx, randomMember)


    async def getRandomMember(self, ctx):
        players = self.get(ctx.guild.id, "players")

        player_members = []

        for player in players:
            player_members.append(discord.utils.get(
                ctx.guild.members, name=player))

        # TODO: instead, choose a random index in [0, arr_size - 1] and use that.
        # no need to shuffle
        m = np.array(player_members)
        np.random.shuffle(m)

        return m[0]


    # helper fn for choosing team members from players that haven't been chosen
    # TODO: using capNum sounds messy. why not just use their id?
    async def chooseHelper(self, ctx, member, capNum):
        # TODO: remove result1, result2
        captain1 = self.get(ctx.guild.id, "captain1")
        captain2 = self.get(ctx.guild.id, "captain2")
        players = self.get(ctx.guild.id, "players")
        team1 = self.get(ctx.guild.id, "team1")
        team2 = self.get(ctx.guild.id, "team2")
        result1 = self.get(ctx.guild.id, "result1")
        result2 = self.get(ctx.guild.id, "result2")
        ids = self.get(ctx.guild.id, "ids")

        captain1 = discord.utils.get(ctx.guild.members, id=captain1id)
        captain2 = discord.utils.get(ctx.guild.members, id=captain2id)

        channel = ctx.message.author.voice.channel
        # TODO: what is the purpose of switch?
        switch = True

        if (
            member not in team1
            and member not in team2
            and member.name in players
        ):
            if capNum == 1:
                result1 += "\n" + member.name
                team1.append(member.name)
                self.update(ctx.guild.id, "team1", team1)
                self.update(ctx.guild.id, "result1", result1)
            else:
                result2 += "\n" + member.name
                team2.append(member.name)
                self.update(ctx.guild.id, "team2", team2)
                self.update(ctx.guild.id, "result2", result2)

            players.remove(member.name)
            ids.append(member.id)

            self.update(ctx.guild.id, "players", players)
            self.update(ctx.guild.id, "ids", ids)

            await self.printEmbed(ctx, channel)
        else:
            # TODO: cleanup this if-else ladder
            switch = False
            await ctx.response.send_message(
                "Player has already been selected or does not exist in the player list."
            )

        if players == []:
            await ctx.response.send_message(
                'You\'ve drafted the maximum number of people for the team size! Use ".move" to move everyone to the channels!'
            )
            return

        if capNum == 2 and switch:
            self.update(ctx.guild.id, "captainNum", 1)
            await ctx.response.send_message(
                captain1.mention + ', use "/choose  @_____" to pick a player for your team'
            )
        elif capNum == 1 and switch:
            self.update(ctx.guild.id, "captainNum", 2)
            await ctx.response.send_message(
                captain2.mention + ', use "/choose  @_____" to pick a player for your team'
            )
        else:
            if capNum == 1:
                await ctx.response.send_message(
                    captain1.mention
                    + ', type "/use  @_____" to pick a player for your team'
                )
            else:
                await ctx.response.send_message(
                    captain2.mention
                    + ', use "/choose  @_____" to pick a player for your team'
                )


    # TODO: RENAME THIS TO SOMETHING REAL ????
    # sets up teams and moves them into respective channels
    async def all(self, ctx, team1, team2):
        await self.printEmbed(ctx)
        await self.setTeamHelper(ctx, team1, team2)
        await self.movefunc(ctx)


    # clears all current teams
    async def clearTeamsHelper(self, ctx):
        guild_id = ctx.guild.id

        # TODO: remove unused columns
        self.update(guild_id, "original_channel", "")
        self.update(guild_id, "team1", "")
        self.update(guild_id, "team2", "")
        self.update(guild_id, "players", "")
        self.update(guild_id, "team_size", 5)
        self.update(guild_id, "mode", "Normal")
        self.update(guild_id, "turn", 1)

    async def notifyHelper(self, ctx, member: discord.Member):
        team_size = self.get(ctx.guild.id, "team_size")
        channel = await member.create_dm()
        invite_channel = ctx.user.voice.channel
        invite_link = await invite_channel.create_invite(max_uses=1, unique=True)
        content = (
            ctx.user.global_name
            + " has invited you to a "
            + str(team_size * 2)
            + " man!\n\n"
            + str(invite_link)
        )
        await channel.send(content)
