import kivy
kivy.require("1.8.0")
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
import time
from kivy.graphics import Color
from kivy.app import App
from kivy.uix.widget import Widget
import random
from kivy.clock import Clock, partial
from math import sqrt, ceil


"""
Super Memory Game by Aaron Nhan for Kleiner-Perkins Application

The first part is kivy language code and the second part is Python
"""

#Kivy Code integrates with Python when the python class calls the Superclass constructor

Builder.load_string("""
<Deck>:

<Game>:
    size_hint: 1,1
    GridLayout:
        size: root.grid_size
        id: game_layout
        cols: root.cards_per_row
        rows: root.cards_per_row
        pos: 0, root.start_button_buffer
    Label:
        id: score_label
        pos: root.window_width, root.window_height
        font_size: "20sp"
    AnchorLayout:
        size: root.size
        anchor_x: "center"
        anchor_y: "bottom"
        BoxLayout:
            orientation: "horizontal"
            Button:
                size_hint: (.5, .1)
                text: "New Game"
                on_release: root.start_game()
            Button:
                size_hint: (.5, .1)
                text: "Flip Cards"
                on_release: 
                    root.flip_cards()
                    root.point_callback()

<Card>:
    Button:
        color: 0,0,0,1
        id: card_button
        center: root.center
        size: root.size
""")

#Class definition for Card Class that creates functionality
class Card(Widget):
    def __init__(self, suit, value, **kwargs):
        super(Card, self).__init__(**kwargs)
        self.suit = suit
        self.value = value
        self.back_flip_counter = 1
        self.front_flip_counter = 1
        self.flippable = True
        #Paths to atlas with images for selecting and deselecting cards
        self.back_flip_list = ["atlas://data/images/defaulttheme/button",
                               "atlas://data/images/defaulttheme/button_pressed"]
        #Paths to atlas with images for when you flip over card
        self.front_flip_list = ["atlas://data/images/defaulttheme/button", 
                               "atlas://card_pics/cardatlas/" + str(self.suit) + str(self.value)]
    #Changes background image of button when selected
    def toggle_select_background(self):
        self.ids["card_button"].background_normal = self.back_flip_list[self.back_flip_counter]
        self.back_flip_counter = abs(self.back_flip_counter-1)

    #Changes background image of button when flipped
    def flip(self):
        if self.flippable:
            self.ids["card_button"].background_normal = ("atlas://card_pics/cardatlas/"
                                                         + str(self.suit) + str(self.value))
        else:
            self.ids["card_button"].background_normal = "atlas://data/images/defaulttheme/button"

#Class that distributes shuffled Cards
class Deck(Widget):
    def __init__(self, **kwargs):
        super(Deck, self).__init__(**kwargs)
        deck_capacity = 52
        num_suits = 4
        num_values = 13
        self.deck = [[suit,value] for suit in range(num_suits) for value in range(num_values)]
        random.shuffle(self.deck)
    def draw_cards(self, num_cards):
        drawn_cards = self.deck[0:num_cards]
        return drawn_cards

#Main class
class Game(Widget):
    def __init__(self, num_cards, **kwargs):
        self.suit_index = 0
        self.value_index = 1
        self.matching_list = []
        self.num_cards = num_cards
        self.card_size = (146, 196)

        #automatically adjusts window size numbers based on number of cards
        buffer_ratio = .15
        self.cards_per_row = int(ceil(sqrt(num_cards)))           
        self.window_height = self.cards_per_row*self.card_size[1]
        self.window_width = self.cards_per_row*self.card_size[0]
        self.window_side_buffer = buffer_ratio*self.window_width
        self.score_width = 300
        self.start_button_buffer = buffer_ratio*self.window_height

        #Creates layout for cards and adjusts positioning
        self.layout_center = (self.window_width/2, 
                              self.window_height/2 + self.start_button_buffer)
        self.grid_size = (self.window_width*(1-buffer_ratio), 
                          self.window_height*(1-buffer_ratio))
        self.size = self.grid_size

        #Calls kivy code and sets window size
        super(Game, self).__init__(**kwargs)
        Window.size = (self.width + self.score_width, 
                       self.window_height + self.start_button_buffer)

    #Called every time a new game is started
    def start_game(self):

        #Sets up cards for playing
        self.ids["score_label"].text = "Memorizing Time!"
        self.points = 0
        self.my_deck = Deck()
        self.my_cards = self.my_deck.draw_cards(self.num_cards)
        self.ids["game_layout"].clear_widgets()
        for i in range(self.num_cards):
            card = Card(self.my_cards[i][self.suit_index], 
                        self.my_cards[i][self.value_index])
            card.ids["card_button"].bind(on_release = self.card_callback)
            self.ids["game_layout"].add_widget(card)

        #Reveals cards to user for memorization and sets up timer to turn cards facedown
        self.flipall()
        Clock.schedule_once(self.flipall, self.num_cards)

        #Calculates a goal time to beat
        self.goal_list = []
        self.calculate_goal()
        self.computer_points = self.calculate_computer_points()

    #Function to flip all cards on the table
    def flipall(self, *args):
        for x in self.ids["game_layout"].children: #game_layout only recieves cards as children
            x.flip()
            x.flippable = not x.flippable
            print x.flippable

    #Sorting Algorithm based on counting sort O(n), fast with few elements, no need for data structures
    def sort_cards(self, card_list):
        return_list = []
        count_list = [[] for i in range(13)]
        for x in card_list:
            if type(x) is Card:
                count_list[x.value].append(x)
            else:
                count_list[x[1]].append(x)
        for x in count_list:
            for y in x: 
                return_list.append(y)
        return return_list #Sorted based on values but not suits.

    #Callback function for pressing a card. Determines background image of card and manages matching_list
    #matching_list is the list of cards currently selected.
    def card_callback(self, card_button):
        card = card_button.parent
        if card.flippable:
            card.toggle_select_background()
            if card in self.matching_list:
                self.matching_list.remove(card)
            else:
                self.matching_list.append(card)

    #Flips cards and calculates points when user presses "flip cards" button
    def flip_cards(self):
        #If there is only one card left, add a dummy card
        if len(self.matching_list) == 1:
            self.matching_list.append(Card(0,0))
        #calculates points and flips
        self.matching_list = self.sort_cards(self.matching_list)
        for x in range(len(self.matching_list)):
            self.points += self.pointify(self.matching_list[0].value, 
                              self.matching_list[x].value, 
                              self.matching_list[-1].value)
            self.matching_list[x].flip()
            self.matching_list[x].flippable = False
        self.matching_list = []

    #The next few methods are for calculating a goal time
    def calculate_goal(self): 
        #self.goal_list will become a list of lists that contain the pairings [[pairing1],[pairing2]]
        self.goal_list = []
        #Sorts cards by value
        self.my_cards = self.sort_cards(self.my_cards)

        #by removing the second to last card we can guarantee that the last card has a pair
        placeholder = self.my_cards[len(self.my_cards)-2]
        self.my_cards = self.my_cards[0:len(self.my_cards)-2] + [self.my_cards[-1]]

        #Does calculation then adds second to last card back to pair up with last card.
        self.recursive_calculation1(self.my_cards)
        self.goal_list[0].append(placeholder)

    #Creates a pair with the first two elements in the list and calls recursive_calculation2
    #to decide how many more elements will be added to the pairing before starting a new one. 
    #Keeps on repeating until all elements are gone.
    def recursive_calculation1(self, card_list):

        #If the value that will be decided to go into the pairing has no number to the right
        #then put it into the pairing so it isn't alone
        if len(card_list) <= 3:
            return card_list

        #If the value that will be decided to go into the pairing has a number to right, call 
        #recursive_calculation2 to determine how many values will go into the pairing
        else: 
            self.goal_list.append(card_list[0:2] + self.recursive_calculation2(card_list, 2))

    #Is called on to complete the pairings from recursive_calculation1.
    #The index keeps track of which value is being tested
    #Calls on recursive_calculation1 to start a new pairing when it finishes the current pairing   
    def recursive_calculation2(self, card_list, index):

        #If the index is the last index, add its element to the pairing so it has a pairing
        #Necessary as recursive calls change index and can create out of bounds
        if len(card_list) == index+1:
            self.goal_list.append([card_list[index]])
            return []

        #If the value should go in the pairing, return the value and call itself to determine the next pairing 
        if card_list[index][1] - card_list[0][1] <= card_list[index+1][1] - card_list[index][1]:
            return [card_list[index]] + self.recursive_calculation2(card_list, index+1)

        #If the value shouldn't go into the pairing, make a call to recursive_calculation1 to start a new one
        self.recursive_calculation1(card_list[index::])
        return []

    #calculates goal points
    def calculate_computer_points(self):
        points = 0
        for x in range(len(self.goal_list)):
            for y in range(len(self.goal_list[x])):
                points += self.pointify(self.goal_list[x][0][1], 
                                        self.goal_list[x][y][1], 
                                        self.goal_list[x][-1][1])
        return points
    
    #Whenever points change, change the current player points
    def point_callback(self, *args):
        self.ids["score_label"].text = "Goal: under " + str(self.computer_points) + "\n Points: " + str(self.points)
    #calculates the max difference of card values for each card in a list and squares it.
    def pointify(self, under, index, over):
        return max(index-under, over-index)**2


class MemoryGame(App):
    def build(self):
        #Number of cards on table. Works from 5 to 52 if you have a big enough monitor.
        cards_on_table = 30
        if cards_on_table <= 52 and cards_on_table >=5: 
            return Game(cards_on_table)
        raise ValueError

if __name__ == '__main__':
    MemoryGame().run()
