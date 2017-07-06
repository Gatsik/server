import logging

from server.abc.base_game import InitMode
from server.players import Player
from .game import Game, ValidityState

logger = logging.getLogger(__name__)


class LadderGame(Game):
    """Class for 1v1 ladder games"""
    init_mode = InitMode.AUTO_LOBBY

    def __init__(self, id, *args, **kwargs):
        super(self.__class__, self).__init__(id, *args, **kwargs)
        self.game_mode = 'ladder1v1'
        self.max_players = 2

    async def rate_game(self):
        if self.validity == ValidityState.VALID:
            new_ratings = self.compute_rating(rating='ladder')

            await self.persist_rating_change_stats(new_ratings, rating='ladder')
            await self._update_division_scores()

    async def _update_division_scores(self):
        for player in self.players:
            army = self.get_player_option(player.id, 'Army')
            try:
                if self.get_army_score(army) == 1:
                    winner = player
                if self.get_army_score(army) == 0:
                    loser = player
            except KeyError:
                return

        if winner is not None:
            self.game_service.game_stats_service.process_ladder_scores(winner, loser, 1)

    def is_winner(self, player: Player):
        return self.get_army_score(self.get_player_option(player.id, 'Army')) > 0

    async def on_game_end(self):
        await super().on_game_end()
        if self.validity != ValidityState.VALID:
            return

    @property
    def is_draw(self):
        for army in self.armies:
            for result in self._results[army]:
                if result[1] == 'draw':
                    return True
        return False

    def get_army_score(self, army):
        """
        The head-to-head matchup ranking uses only win/loss as a factor
        :param army:
        :return:
        """
        if army not in self._results:
            return 0

        for result in self._results[army]:
            if result[1] == 'victory':
                return 1
        return 0
