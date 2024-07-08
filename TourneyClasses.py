import discord

class Team:
    def __init__(self) -> None:
        self.id = None
        self.name = None
        self.players = []
        self.size = 0
        self.voice_channel = None
        self.captain = None

    def add_player(self, player: discord.Member) -> None:
        self.players.append(player)
        self.size += 1

    def remove_player(self, player: discord.Member) -> None:
        self.players.remove(player)
        self.size -= 1

    def set_name(self, name: str) -> None:
        self.name = name

    def set_score(self, score: int) -> None:
        self.score = score

    def set_winner(self, winner: bool) -> None:
        self.winner = winner

    def set_voice_channel(self, voice_channel: discord.VoiceChannel) -> None:
        self.voice_channel = voice_channel

    def set_captain(self, captain: discord.Member) -> None:
        self.captain = captain

    def set_id(self, id: int) -> None:
        self.id = id

    def get_id(self) -> int:
        return self.id 

    def get_name(self) -> str:
        return self.name

    def get_players(self) -> list:
        return self.players

    def get_score(self) -> int:
        return self.score

    def get_winner(self) -> bool:
        return self.winner
    
    def get_voice_channel(self) -> discord.VoiceChannel:
        return self.voice_channel
    
    def get_captain(self) -> discord.Member:
        return self.captain
    
    def get_size(self) -> int:
        return self.size

class Match:
    def __init__(self) -> None:
        self.team1 = None
        self.team2 = None
        self.finished = False
        self.winner = None

class Tournament():
    def __init__(self) -> None:
        pass