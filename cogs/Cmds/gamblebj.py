
import discord
from discord.ext import commands
import random
from typing import List, Dict


class BlackjackView(discord.ui.View):
    def __init__(self, ctx, cog):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.cog = cog
        self.selected_stakes = None
        self.started = False

    @discord.ui.select(
        placeholder="Select Stakes",
        options=[
            discord.SelectOption(
                label="Low Stakes", 
                description="500k - 5m per hand", 
                value="low",
                emoji="💰"
            ),
            discord.SelectOption(
                label="High Stakes", 
                description="5m - 50m per hand", 
                value="high",
                emoji="🎰"
            )
        ]
    )
    async def select_stakes(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your game!", ephemeral=True)
            return

        self.selected_stakes = select.values[0]
        
        if self.selected_stakes == "low":
            embed = discord.Embed(
                title="🃏 Low Stakes Blackjack",
                description="Classic blackjack with lower betting limits",
                color=discord.Color.gold()
            )
            embed.add_field(
                name="Betting Limits",
                value=f"• Minimum Bet: {self.cog.format_amount(500000)}\n• Maximum Bet: {self.cog.format_amount(5000000)}",
                inline=False
            )
        else:
            embed = discord.Embed(
                title="🃏 High Stakes Blackjack",
                description="High roller blackjack with bigger risks and rewards",
                color=discord.Color.gold()
            )
            embed.add_field(
                name="Betting Limits",
                value=f"• Minimum Bet: {self.cog.format_amount(5000000)}\n• Maximum Bet: {self.cog.format_amount(50000000)}",
                inline=False
            )

        embed.add_field(
            name="Rules",
            value=(
                "• Blackjack pays 3:2\n"
                "• Dealer must stand on 17\n"
                "• Double down available on any first two cards\n"
                "• Split pairs allowed (up to 2 times)\n"
                "• Insurance available when dealer shows Ace"
            ),
            inline=False
        )

        self.children[1].disabled = False
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.green, disabled=True)
    async def start_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your game!", ephemeral=True)
            return

        self.started = True
        self.stop()
        await interaction.response.defer()

class BettingView(discord.ui.View):
    def __init__(self, ctx, cog, stakes):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.cog = cog
        self.stakes = stakes
        self.bet_amount = None

    @discord.ui.button(label="Min Bet", style=discord.ButtonStyle.blurple)
    async def min_bet(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your game!", ephemeral=True)
            return

        self.bet_amount = self.min_bet
        
        for item in self.children:
            item.disabled = True
            
        embed = discord.Embed(
            title="Blackjack",
            description=f"Bet amount: {self.cog.format_amount(self.bet_amount)}",
            color=discord.Color.green()
        )
        
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    @discord.ui.button(label="Max Bet", style=discord.ButtonStyle.blurple)
    async def max_bet(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your game!", ephemeral=True)
            return

        self.bet_amount = self.max_bet
        
        for item in self.children:
            item.disabled = True
            
        embed = discord.Embed(
            title="Blackjack",
            description=f"Bet amount: {self.cog.format_amount(self.bet_amount)}",
            color=discord.Color.green()
        )
        
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    @discord.ui.button(label="Custom Bet", style=discord.ButtonStyle.green)
    async def custom_bet(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your game!", ephemeral=True)
            return

        modal = CustomBetModal(self.stakes, self.cog)
        await interaction.response.send_modal(modal)
        await modal.wait()

        if modal.bet_amount:
            balance = await self.cog.economy.get_balance(str(self.ctx.author.id))
            if balance < modal.bet_amount:
                await interaction.followup.send(
                    f"You don't have enough balance! You need {self.cog.format_amount(modal.bet_amount)}", 
                    ephemeral=True
                )
                return

            await self.cog.remove_balance(str(self.ctx.author.id), modal.bet_amount)
            
            self.bet_amount = modal.bet_amount
            self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, row=1)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your game!", ephemeral=True)
            return

        self.bet_amount = None
        self.stop()
        await interaction.response.defer()

class CustomBetModal(discord.ui.Modal, title="Place Your Bet"):
    def __init__(self, stakes, cog):
        super().__init__()
        self.stakes = stakes
        self.cog = cog
        self.bet_amount = None

        self.bet_input = discord.ui.TextInput(
            label="Bet Amount",
            placeholder="Enter amount (e.g., 1M, 2.5M)",
            required=True,
            max_length=20
        )
        self.add_item(self.bet_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = self.cog.parse_amount(self.bet_input.value)
            min_bet = 500_000 if self.stakes == "low" else 5_000_000
            max_bet = 5_000_000 if self.stakes == "low" else 50_000_000

            if amount < min_bet:
                await interaction.response.send_message(
                    f"Minimum bet is {self.cog.format_amount(min_bet)}!", 
                    ephemeral=True
                )
                return

            if amount > max_bet:
                await interaction.response.send_message(
                    f"Maximum bet is {self.cog.format_amount(max_bet)}!", 
                    ephemeral=True
                )
                return

            self.bet_amount = amount
            await interaction.response.defer()

        except ValueError:
            await interaction.response.send_message(
                "Invalid amount format! Use numbers with K, M, B, or T (e.g., 1.5K, 2M, 3B)", 
                ephemeral=True
            )



class BlackjackGame:
    def __init__(self, ctx, cog, bet_amount):
        self.ctx = ctx
        self.cog = cog
        self.bet_amount = bet_amount
        self.deck = []
        self.player_hands = [[]]
        self.dealer_hand = []
        self.current_hand = 0
        self.game_over = False
        self.state = "starting"
        self.create_deck()
    async def start_game(self):
        
        dealer_value = self.calculate_hand(self.dealer_hand)
        player_value = self.calculate_hand(self.player_hands[0])
        
        if dealer_value == 21 and player_value == 21:
            self.state = "push"
            return "push"
        elif dealer_value == 21:
            self.state = "dealer_blackjack"
            return "dealer_blackjack"
        elif player_value == 21:
            self.state = "player_blackjack"
            return "player_blackjack"
            
        self.state = "player_turn"
        return "continue"

    async def dealer_turn(self):
        self.state = "dealer_turn"
        while self.calculate_hand(self.dealer_hand) < 17:
            self.dealer_hand.append(self.deal_card())
        return self.calculate_results()

    def calculate_results(self):
        results = []
        dealer_value = self.calculate_hand(self.dealer_hand)
        
        for i, hand in enumerate(self.player_hands):
            hand_value = self.calculate_hand(hand)
            bet = self.bet_amount if i == 0 else self.bet_amount
            
            if hand_value > 21:
                results.append({"hand": i, "result": "BUST", "payout": 0})
            elif len(hand) == 2 and hand_value == 21:
                results.append({"hand": i, "result": "BLACKJACK", "payout": int(bet * 2.5)})
            elif dealer_value > 21 or hand_value > dealer_value:
                results.append({"hand": i, "result": "WIN", "payout": bet * 2})
            elif hand_value == dealer_value:
                results.append({"hand": i, "result": "PUSH", "payout": bet})
            else:
                results.append({"hand": i, "result": "LOSE", "payout": 0})
                
        return results

    def create_deck(self):
        suits = ['♠️', '♥️', '♦️', '♣️']
        values = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        self.deck = [f"{value}{suit}" for suit in suits for value in values] * 6
        random.shuffle(self.deck)

    def deal_card(self):
        return self.deck.pop()

    def calculate_hand(self, hand):
        value = 0
        aces = 0
        
        for card in hand:
            card_value = card[:-2]
            if card_value in ['J', 'Q', 'K']:
                value += 10
            elif card_value == 'A':
                aces += 1
            else:
                value += int(card_value)
        
        for _ in range(aces):
            if value + 11 <= 21:
                value += 11
            else:
                value += 1
                
        return value

    def can_split(self):
        hand = self.player_hands[self.current_hand]
        if len(hand) != 2:
            return False
        return hand[0][:-2] == hand[1][:-2]

    def format_hand(self, hand, hide_second=False):
        if hide_second and len(hand) > 1:
            return f"{hand[0]} 🂠"
        return " ".join(hand)

    async def create_game_embed(self, show_dealer=False):
        embed = discord.Embed(title="🎰 Blackjack", color=discord.Color.gold())
        
        dealer_cards = self.format_hand(self.dealer_hand, not show_dealer)
        dealer_value = self.calculate_hand(self.dealer_hand) if show_dealer else "?"
        embed.add_field(
            name=f"Dealer's Hand ({dealer_value})",
            value=dealer_cards,
            inline=False
        )

        for i, hand in enumerate(self.player_hands):
            current = "👉 " if i == self.current_hand and not self.game_over else ""
            hand_value = self.calculate_hand(hand)
            embed.add_field(
                name=f"{current}Your Hand {i+1} ({hand_value})",
                value=self.format_hand(hand),
                inline=False
            )

        embed.add_field(
            name="Bet Amount",
            value=self.cog.format_amount(self.bet_amount),
            inline=False
        )

        return embed

class GameView(discord.ui.View):
    async def start_game(self):
        result = await self.game.start_game()
        
        if result != "continue":
            await self.handle_early_end(result)
            return
                
        self.update_buttons()
            
    async def handle_early_end(self, result):
        if result == "push":
            await self.cog.add_balance(str(self.ctx.author.id), self.game.bet_amount)
            winnings = 0
        elif result == "player_blackjack":
            payout = int(self.game.bet_amount * 2.5)
            await self.cog.add_balance(str(self.ctx.author.id), payout)
            winnings = payout - self.game.bet_amount
        else:
            winnings = -self.game.bet_amount
                
        embed = await self.game.create_game_embed(show_dealer=True)
        embed.add_field(
            name="Result",
            value=f"{result.replace('_', ' ').title()}\nNet profit: {self.cog.format_amount(winnings)}",
            inline=False
        )
            
        for item in self.children:
            item.disabled = True
        await self.message.edit(embed=embed, view=self)

    async def end_game(self, interaction):
        self.game.game_over = True
        
        while self.game.calculate_hand(self.game.dealer_hand) < 17:
            self.game.dealer_hand.append(self.game.deal_card())

        dealer_value = self.game.calculate_hand(self.game.dealer_hand)
        
        total_winnings = 0
        results = []
        
        for i, hand in enumerate(self.game.player_hands):
            hand_value = self.game.calculate_hand(hand)
            bet = self.game.bet_amount if i == 0 else self.game.bet_amount
            
            if hand_value > 21:
                result = "BUST"
                winnings = 0
            elif len(hand) == 2 and hand_value == 21:
                result = "BLACKJACK"
                winnings = int(bet * 2.5)
            elif dealer_value > 21 or hand_value > dealer_value:
                result = "WIN"
                winnings = bet * 2
            elif hand_value == dealer_value:
                result = "PUSH"
                winnings = bet
            else:
                result = "LOSE"
                winnings = 0
                
            total_winnings += winnings
            results.append(f"Hand {i+1}: {result} ({'+' if winnings > bet else ''}{self.cog.format_amount(winnings - bet)})")

        if total_winnings > 0:
            await self.cog.add_balance(str(self.ctx.author.id), total_winnings)

        embed = await self.game.create_game_embed(show_dealer=True)
        embed.add_field(name="Results", value="\n".join(results), inline=False)
        
        net_profit = total_winnings - (self.game.bet_amount * len(self.game.player_hands))
        embed.add_field(
            name="Net Profit",
            value=f"{'+' if net_profit > 0 else ''}{self.cog.format_amount(net_profit)}",
            inline=False
        )

        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)


    def update_buttons(self):
        hand = self.game.player_hands[self.game.current_hand]
        hand_value = self.game.calculate_hand(hand)
        
        if self.game.game_over or hand_value >= 21:
            for item in self.children:
                item.disabled = True
            return

   
   

        self.children[3].disabled = not self.game.can_split()
        
        self.children[2].disabled = len(hand) != 2

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.blurple, emoji="🎯")
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your game!", ephemeral=True)
            return

        current_hand = self.game.player_hands[self.game.current_hand]
        current_hand.append(self.game.deal_card())
        
        if self.game.calculate_hand(current_hand) > 21:
            if self.game.current_hand < len(self.game.player_hands) - 1:
                self.game.current_hand += 1
            else:
                await self.end_game(interaction)
                return

        self.update_buttons()
        await interaction.response.edit_message(embed=await self.game.create_game_embed(), view=self)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.green, emoji="✋")
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your game!", ephemeral=True)
            return

        if self.game.current_hand < len(self.game.player_hands) - 1:
            self.game.current_hand += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=await self.game.create_game_embed(), view=self)
        else:
            await self.end_game(interaction)

    @discord.ui.button(label="Double", style=discord.ButtonStyle.gray, emoji="💰")
    async def double(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your game!", ephemeral=True)
            return

        balance = await self.cog.get_balance(str(self.ctx.author.id))
        if balance < self.game.bet_amount:
            await interaction.response.send_message("Not enough balance to double!", ephemeral=True)
            return

        await self.cog.remove_balance(str(self.ctx.author.id), self.game.bet_amount)
        self.game.bet_amount *= 2

        current_hand = self.game.player_hands[self.game.current_hand]
        current_hand.append(self.game.deal_card())

        if self.game.current_hand < len(self.game.player_hands) - 1:
            self.game.current_hand += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=await self.game.create_game_embed(), view=self)
        else:
            await self.end_game(interaction)

    @discord.ui.button(label="Split", style=discord.ButtonStyle.gray, emoji="✂️")
    async def split(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your game!", ephemeral=True)
            return

        balance = await self.cog.get_balance(str(self.ctx.author.id))
        if balance < self.game.bet_amount:
            await interaction.response.send_message("Not enough balance to split!", ephemeral=True)
            return

        await self.cog.remove_balance(str(self.ctx.author.id), self.game.bet_amount)
        
        current_hand = self.game.player_hands[self.game.current_hand]
        new_hand = [current_hand.pop()]
        self.game.player_hands.append(new_hand)
        
        current_hand.append(self.game.deal_card())
        new_hand.append(self.game.deal_card())

        self.update_buttons()
        await interaction.response.edit_message(embed=await self.game.create_game_embed(), view=self)

    async def end_game(self, interaction):
        self.game.game_over = True
        
        while self.game.calculate_hand(self.game.dealer_hand) < 17:
            self.game.dealer_hand.append(self.game.deal_card())

        dealer_value = self.game.calculate_hand(self.game.dealer_hand)
        
        total_winnings = 0
        results = []
        
        for i, hand in enumerate(self.game.player_hands):
            hand_value = self.game.calculate_hand(hand)
            bet = self.game.bet_amount if i == 0 else self.game.bet_amount
            
            if hand_value > 21:
                result = "BUST"
                winnings = 0
            elif len(hand) == 2 and hand_value == 21:
                result = "BLACKJACK"
                winnings = int(bet * 2.5)
            elif dealer_value > 21 or hand_value > dealer_value:
                result = "WIN"
                winnings = bet * 2
            elif hand_value == dealer_value:
                result = "PUSH"
                winnings = bet
            else:
                result = "LOSE"
                winnings = 0
                
            total_winnings += winnings
            results.append(f"Hand {i+1}: {result} ({'+' if winnings > bet else ''}{self.cog.format_amount(winnings - bet)})")

        if total_winnings > 0:
            await self.cog.add_balance(str(self.ctx.author.id), total_winnings)

        embed = await self.game.create_game_embed(show_dealer=True)
        embed.add_field(name="Results", value="\n".join(results), inline=False)
        
        net_profit = total_winnings - (self.game.bet_amount * len(self.game.player_hands))
        embed.add_field(
            name="Net Profit",
            value=f"{'+' if net_profit > 0 else ''}{self.cog.format_amount(net_profit)}",
            inline=False
        )

        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)


class Blackjack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}
        self.state = "starting"



    async def start_game(self):
        self.player_hands[0] = [self.deal_card(), self.deal_card()]
        self.dealer_hand = [self.deal_card(), self.deal_card()]
        
        dealer_value = self.calculate_hand(self.dealer_hand)
        player_value = self.calculate_hand(self.player_hands[0])
        
        if dealer_value == 21 and player_value == 21:
            self.state = "push"
            return "push"
        elif dealer_value == 21:
            self.state = "dealer_blackjack"
            return "dealer_blackjack"
        elif player_value == 21:
            self.state = "player_blackjack"
            return "player_blackjack"
            
        self.state = "player_turn"
        return "continue"

    async def player_turn(self):
        pass

    async def dealer_turn(self):
        self.state = "dealer_turn"
        while self.calculate_hand(self.dealer_hand) < 17:
            self.dealer_hand.append(self.deal_card())
        return self.calculate_results()

    def calculate_results(self):
        results = []
        dealer_value = self.calculate_hand(self.dealer_hand)
        
        for i, hand in enumerate(self.player_hands):
            hand_value = self.calculate_hand(hand)
            bet = self.bet_amount if i == 0 else self.bet_amount
            
            if hand_value > 21:
                results.append({"hand": i, "result": "BUST", "payout": 0})
            elif len(hand) == 2 and hand_value == 21:
                results.append({"hand": i, "result": "BLACKJACK", "payout": int(bet * 2.5)})
            elif dealer_value > 21 or hand_value > dealer_value:
                results.append({"hand": i, "result": "WIN", "payout": bet * 2})
            elif hand_value == dealer_value:
                results.append({"hand": i, "result": "PUSH", "payout": bet})
            else:
                results.append({"hand": i, "result": "LOSE", "payout": 0})
                
        return results
    
    async def process_results(self):
        dealer_total = self.calculate_hand(self.dealer_hand)
        for i, hand in enumerate(self.player_hands):
            player_total = self.calculate_hand(hand)

    def get_economy_cog(self):
        return self.bot.get_cog('Economy')

    @commands.command(name="blackjack", aliases=["bj"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def blackjack(self, ctx, amount: str = None):
        economy = self.bot.get_cog('Economy')

        if amount is None:
            await ctx.send("Please specify the amount to bet!")
            return
        

        balance = await self.economy.get_balance(str(ctx.author.id))
        if balance <= 0:
            await ctx.send("You don't have any money to play!")
            return

        stakes_view = BlackjackView(ctx)
        message = await ctx.send(
            embed=discord.Embed(
                title="Blackjack",
                description="Choose your stakes:",
                color=discord.Color.green()
            ),
            view=stakes_view
        )
        stakes_view.message = message

        await stakes_view.wait()
        
        if stakes_view.value is None:
            await message.edit(
                content="Game cancelled due to timeout.",
                embed=None,
                view=None
            )
            return

        if stakes_view.value == "low":
            min_bet = 500_000
            max_bet = 5_000_000
        else:
            min_bet = 5_000_000
            max_bet = 50_000_000

        if balance < min_bet:
            await message.edit(
                content=f"You need at least {self.format_amount(min_bet)} to play at these stakes!",
                embed=None,
                view=None
            )
            return

        betting_view = BettingView(ctx, self, min_bet, max_bet)
        await message.edit(
            content=None,
            embed=discord.Embed(
                title="Blackjack",
                description="Choose your bet amount:",
                color=discord.Color.green()
            ),
            view=betting_view
        )
        betting_view.message = message

        await betting_view.wait()

        if betting_view.bet_amount is None:
            await message.edit(
                content="Game cancelled due to timeout.",
                embed=None,
                view=None
            )
            return

        current_balance = await self.economy.get_balance(str(ctx.author.id))
        if current_balance < betting_view.bet_amount:
            await message.edit(
                content="You don't have enough money for this bet!",
                embed=None,
                view=None
            )
            return

        await self.remove_balance(str(ctx.author.id), betting_view.bet_amount)

        game = BlackjackGame(ctx, self, betting_view.bet_amount)
        game_view = GameView(ctx, self, game)
        
        message = await message.edit(
            content=None,
            embed=await game.create_game_embed(),
            view=game_view
        )
        game_view.message = message
        await game_view.start_game()

        await game_view.wait()

        if not game.game_over:
            await message.edit(
                content="Game cancelled due to timeout.",
                embed=None,
                view=None
            )
            await self.add_balance(str(ctx.author.id), betting_view.bet_amount)

async def setup(bot):
    await bot.add_cog(Blackjack(bot))