import socket
import random


class AuctionClient(object):
    """A client for bidding with the AucionRoom"""
    def __init__(self, host="localhost", port=8020, mybidderid=None, verbose=False):
        self.verbose = verbose
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host,port))
        forbidden_chars = set(""" '".,;:{}[]()""")
        if mybidderid:
            if len(mybidderid) == 0 or any((c in forbidden_chars) for c in mybidderid):
                print("""mybidderid cannot contain spaces or any of the following: '".,;:{}[]()!""")
                raise ValueError
            self.mybidderid = mybidderid
        else:
            self.mybidderid = raw_input("Input team / player name : ").strip()  # this is the only thing that distinguishes the clients
            while len(self.mybidderid) == 0 or any((c in forbidden_chars) for c in self.mybidderid):
              self.mybidderid = raw_input("""You input an empty string or included a space  or one of these '".,;:{}[]() in your name which is not allowed (_ or / are all allowed)\n for example Emil_And_Nischal is okay\nInput team / player name: """).strip()
        self.sock.send(self.mybidderid.encode("utf-8"))

        data = self.sock.recv(5024).decode('utf_8')
        x = data.split(" ")
        if self.verbose:
            print("Have received response of %s" % ' '.join(x))
        if(x[0] != "Not" and len(data) != 0):
          self.numberbidders = int(x[0])
          if self.verbose:
              print("Number of bidders: %d" % self.numberbidders)
          self.numtypes = int(x[1])
          if self.verbose:
              print("Number of types: %d" % self.numtypes)
          self.numitems = int(x[2])
          if self.verbose:
              print("Items in auction: %d" % self.numitems)
          self.maxbudget = int(x[3])
          if self.verbose:
              print("Budget: %d" % self.maxbudget)
          self.neededtowin = int(x[4])
          if self.verbose:
              print("Needed to win: %d" % self.neededtowin)
          self.order_known = "True" == x[5]
          if self.verbose:
              print("Order known: %s" % self.order_known)
          self.auctionlist = []
          self.winnerpays = int(x[6])
          if self.verbose:
              print("Winner pays: %d" % self.winnerpays)
          self.values = {}
          self.artists = {}
          order_start = 7
          if self.neededtowin > 0:
              self.values = None
              for i in range(7, 7+(self.numtypes*2), 2):
                  self.artists[x[i]] = int(x[i+1])
                  order_start += 2
              if self.verbose:
                  print("Item types: %s" % str(self.artists))
          else:
              for i in range(7, 7+(self.numtypes*3), 3):
                  self.artists[x[i]] = int(x[i+1])
                  self.values[x[i]] = int(x[i+2])
                  order_start += 3
              if self.verbose:
                  print("Item types: %s" % str(self.artists))
                  print ("Values: %s" % str(self.values))

          if self.order_known:
              for i in range(order_start, order_start+self.numitems):
                  self.auctionlist.append(x[i])
              if self.verbose:
                  print("Auction order: %s" % str(self.auctionlist))

        self.sock.send('connected '.encode("utf-8"))

        data = self.sock.recv(5024).decode('utf_8')
        x = data.split(" ")
        if x[0] != 'players':
            print("Did not receive list of players!")
            raise IOError
        if len(x) != self.numberbidders + 2:
            print("Length of list of players received does not match numberbidders!")
            raise IOError
        if self.verbose:
         print("List of players: %s" % str(' '.join(x[1:])))

        self.players = []

        for player in range(1, self.numberbidders + 1):
          self.players.append(x[player])

        self.sock.send('ready '.encode("utf-8"))

        self.standings = {name: {artist : 0 for artist in self.artists} for name in self.players}
        for name in self.players:
          self.standings[name]["money"] = self.maxbudget

    def play_auction(self):
        winnerarray = []
        winneramount = []
        done = False
        while not done:
            data = self.sock.recv(5024).decode('utf_8')
            x = data.split(" ")
            if x[0] != "done":
                if x[0] == "selling":
                    currentitem = x[1]
                    if not self.order_known:
                        self.auctionlist.append(currentitem)
                    if self.verbose:
                        print("Item on sale is %s" % currentitem)
                    bid = self.determinebid(self.numberbidders, self.neededtowin, self.artists, self.values, len(winnerarray), self.auctionlist, winnerarray, winneramount, self.mybidderid, self.players, self.standings, self.winnerpays)
                    if self.verbose:
                        print("Bidding: %d" % bid)
                    self.sock.send(str(bid).encode("utf-8"))
                    data = self.sock.recv(5024).decode('utf_8')
                    x = data.split(" ")
                    if x[0] == "draw":
                        winnerarray.append(None)
                        winneramount.append(0)
                    if x[0] == "winner":
                        self.standings[x[1]][currentitem] += 1
                        self.standings[x[1]]["money"] -= int(x[3])
                        winnerarray.append(x[1])
                        winneramount.append(int(x[3]))
            else:
                done = True
                if self.verbose:
                    if self.mybidderid in x[1:-1]:
                        print("I won! Hooray!")
                    else:
                        print("Well, better luck next time...")
        self.sock.close()

    def determinebid(self, numberbidders, wincondition, artists, values, rd, itemsinauction, winnerarray, winneramount, mybidderid, players, standings, winnerpays):
        '''You have all the variables and lists you could need in the arguments of the function,
        these will always be updated and relevant, so all you have to do is use them.
        Write code to make your bot do a lot of smart stuff to beat all the other bots. Good luck,
        and may the games begin!'''

        '''
        numberbidders is an integer displaying the amount of people playing the auction game.

        wincondition is an integer. A postiive integer means that whoever gets that amount of a single type
        of item wins, whilst 0 means each itemtype will have a value and the winner will be whoever accumulates the
        highest total value before all items are auctioned or everyone runs out of funds.

        artists will be a dict of the different item types as keys with the total number of that type on auction as elements.

        values will be a dict of the item types as keys and the type value if wincondition == 0. Else value == None.

        rd is the current round in 0 based indexing.

        itemsinauction is a list where at index "rd" the item in that round is being sold is displayed. Note that it will either be as long as the sum of all the number of the items (as in "artists") in which case the full auction order is pre-announced and known, or len(itemsinauction) == rd+1, in which case it only holds the past and current items, the next item to be auctioned is unknown.

        winnerarray is a list where at index "rd" the winner of the item sold in that round is displayed.

        winneramount is a list where at index "rd" the amount of money paid for the item sold in that round is displayed.

        example: I will now construct a sentence that would be correct if you substituted the outputs of the lists:
        In round 5 winnerarray[4] bought itemsinauction[4] for winneramount[4] pounds/dollars/money unit.

        mybidderid is your name: if you want to reference yourself use that.

        players is a list containing all the names of the current players.

        standings is a set of nested dictionaries (standings is a dictionary that for each person has another dictionary
        associated with them). standings[name][artist] will return how many paintings "artist" the player "name" currently has.
        standings[name]['money'] (remember quotes for string, important!) returns how much money the player "name" has left.

            standings[mybidderid] is the information about you.
            I.e., standings[mybidderid]['money'] is the budget you have left.

        winnerpays is an integer representing which bid the highest bidder pays. If 0, the highest bidder pays their own bid,
        but if 1, the highest bidder instead pays the second highest bid (and if 2 the third highest, ect....). Note though that if you win, you always pay at least 1 (even if the second-highest was 0).

        Don't change any of these values, or you might confuse your bot! Just use them to determine your bid.
        You can also access any of the object variables defined in the constructor (though again don't change these!), or declare your own to save state between determinebid calls if you so wish.

        determinebid should return your bid as an integer. Note that if it exceeds your current budget (standings[mybidderid]['money']), the auction server will simply set it to your current budget.

        Good luck!
        '''

        # Game 1: First to buy wincondition of any artist wins, highest bidder pays own bid, auction order known.
        if (wincondition > 0) and (winnerpays == 0) and self.order_known:
            return self.first_bidding_strategy(numberbidders, wincondition, artists, values, rd, itemsinauction, winnerarray, winneramount, mybidderid, players, standings, winnerpays)

        # Game 2: First to buy wincondition of any artist wins, highest bidder pays own bid, auction order not known.
        if (wincondition > 0) and (winnerpays == 0) and not self.order_known:
            return self.second_bidding_strategy(numberbidders, wincondition, artists, values, rd, itemsinauction, winnerarray, winneramount, mybidderid, players, standings, winnerpays)

        # Game 3: Highest total value wins, highest bidder pays own bid, auction order known.
        if (wincondition == 0) and (winnerpays == 0) and self.order_known:
            return self.third_bidding_strategy(numberbidders, wincondition, artists, values, rd, itemsinauction, winnerarray, winneramount, mybidderid, players, standings, winnerpays)

        # Game 4: Highest total value wins, highest bidder pays second highest bid, auction order known.
        if (wincondition == 0) and (winnerpays == 1) and self.order_known:
            return self.fourth_bidding_strategy(numberbidders, wincondition, artists, values, rd, itemsinauction, winnerarray, winneramount, mybidderid, players, standings, winnerpays)

        # Though you will only be assessed on these four cases, feel free to try your hand at others!
        # Otherwise, this just returns a random bid.
        return self.random_bid(standings[mybidderid]['money'])

    def random_bid(self, budget):
        """Returns a random bid between 1 and left over budget."""
        return int(budget*random.random()+1)

    def first_bidding_strategy(self, numberbidders, wincondition, artists, values, rd, itemsinauction, winnerarray, winneramount, mybidderid, players, standings, winnerpays):
        """Game 1: First to buy wincondition of any artist wins, highest bidder pays own bid, auction order known."""

        # At the start if I have not buy anything then I am calculating based on the "steps" as I defined in the code the number of
        #times that a paitings is appears in the auction; and based on "counts" the number of selling paitings the first, second , third and fourth
        #artist to be sell 3 times.
        if standings[mybidderid]['money'] == 1000:
            step_P = 0
            step_V = 0
            step_R = 0
            step_D = 0
            count = 0
            countP = 0
            countV = 0
            countR = 0
            countD = 0
            for i in itemsinauction[rd:]: #for all the items to be sold I create a dictionary to save the positiongs as long till all the artists appears 3 times
                if step_P < 3 or step_V < 3 or step_R < 3 or step_D < 3:
                    if i == 'Picasso':
                        step_P += 1
                        count = count + 1
                        if step_P == 3:
                            countP = count #when there is 3 Picassos in the list then the count is saved to define the first and the second artists that appears 3 times
                    elif i == 'Van_Gogh':
                        step_V += 1
                        count = count + 1
                        if step_V == 3:
                            countV = count #when there is 3 Van Gogh in the list then the count is saved to define the first and the second artists that appears 3 times
                    elif i == 'Rembrandt':
                        step_R += 1
                        count = count + 1
                        if step_R == 3:
                            countR = count #when there is 3 Rembrandt in the list then the count is saved to define the first and the second artists that appears 3 times
                    elif i == 'Da_Vinci':
                        step_D += 1
                        count = count + 1
                        if step_D == 3:
                            countD = count #when there is 3 Da Vinci in the list then the count is saved to define the first and the second artists that appears 3 times
                    else:
                        pass
            dic_count = {"Picasso":countP, "Van_Gogh":countV, "Rembrandt":countR, "Da_Vinci":countD} #I save in a dictionary the counts and define the first, second, third and the fourth artist. 
            first = min(dic_count, key=dic_count.get)
            dic_count[first] = 1000
            second = min(dic_count, key=dic_count.get)
            des = 0
            for i in itemsinauction[rd:]:
                if des == 0:
                    if i == second and i != first and numberbidders > 5: #definition of my strategy to go for the second artist in order to apperance if there is a paiting of this second artist to be sell before the first artist and if there is more than 5 players
                        go_for = second
                        des = 1
                    elif i == first: #otherwise go for the first artist in apperance
                        go_for = first
                        des = 1
                    else:
                        pass
        else: #if I have one paint of any artist then I strict to go for that artist
            myPi = standings[mybidderid]['Picasso']
            myVa = standings[mybidderid]['Van_Gogh']
            myRe = standings[mybidderid]['Rembrandt']
            myDa = standings[mybidderid]['Da_Vinci']
            dic_step = {"Picasso":myPi, "Van_Gogh":myVa, "Rembrandt":myRe, "Da_Vinci":myDa}
            go_for = max(dic_step, key=dic_step.get) #get the maximum of the my standings to go for that artists
        curr_item = itemsinauction[rd]
        if curr_item == go_for:
            if standings[mybidderid][curr_item] == 2:
                return standings[mybidderid]['money']
            if standings[mybidderid][curr_item] == 1:
                return int(standings[mybidderid]['money']/2)
            return int(standings[mybidderid]['money']/3)
        else:
            if standings[mybidderid]['money'] == 1000 and itemsinauction[rd:rd+numberbidders*3].count(curr_item)>3 and numberbidders>5:
                return int(standings[mybidderid]['money']/3-2) #in case I do not have any paint, the artist is to be sell more than 3 times in the following 3 times number od bidders order, and the number of bidders is more than 5 then I bid for the third and fourth artist one third of my budget minus 2
            else:
                return 0

    def second_bidding_strategy(self, numberbidders, wincondition, artists, values, rd, itemsinauction, winnerarray, winneramount, mybidderid, players, standings, winnerpays):
        """Game 2: First to buy wincondition of any artist wins, highest bidder pays own bid, auction order not known."""

        total = sum(artists.values())-rd #to calculate the full paintings to be sell
        items_notfin = itemsinauction[:-1] #items sold
        dic_p = {}
        for art in artists.keys():
            p_art = (artists[art]-items_notfin.count(art))/total #this calculates the probability of one artirst to be the next one, by deducting the items sold to the full dictionary with the paiting per artist and dividing it by the full list of items to be sold.
            dic_p[art] = p_art
        #negative binomial for each artist. What's the probability of the 3rd paint to apper at the nth bidding.I want to calculate the expected number of trial given 3 sucess, C(n-1, k-1)*p^k*(1-p)^(n-k) with n the random varible. E(n) = (1-p)k/(p)
        dic_NB = {}
        for art in artists.keys():
            k = wincondition - standings[mybidderid][art] #k defined by the number of sucess that you need to win
            p = dic_p[art]
            dic_NB[art] = (k*(1-p))/(p) #this is the calculation of the expected value of the number of sucesses that you need for win
        import operator
        sort_NB = sorted(dic_NB.items(), key=operator.itemgetter(1)) #the sorted operator sort the dictionary of the expected trial for k sucess by the value
        if abs(sort_NB[0][1]-sort_NB[1][1]) < 2 and numberbidders > 5: #if the difference between the first one and the second one is less than 2 trials and the number of bidders is more than 5 then I am bidding for the second
            go_for = sort_NB[1][0]
        elif abs(sort_NB[0][1]-sort_NB[2][1]) < 3 and numberbidders > 10:#if the number of trials between the first artist and the second artist is less than 3 and the number of bidders is more than 10 then I am bidding for the third artist to appear
            go_for = sort_NB[2][0]
        else:
            go_for = sort_NB[0][0]
        curr_item = itemsinauction[rd]
        for art in artists.keys():
            if standings[mybidderid][art]>0:
                go_for = art #this to define if I have already a pieces of some artists then go for that artist only
        if curr_item == go_for:
            if standings[mybidderid][curr_item] == 2:
                return standings[mybidderid]['money']
            if standings[mybidderid][curr_item] == 1:
                return int(standings[mybidderid]['money']/2)
            return int(standings[mybidderid]['money']/3)
        elif curr_item != go_for and standings[mybidderid]['money'] == 1000 and (artists[curr_item]-items_notfin.count(curr_item)) > 20:
            return int(standings[mybidderid]['money']/3-2) #bid for the number fourth artist one third minus 2 in case there is more than 20 paintings to be sold and if I do not have any piece
        else:
            return 0

    def third_bidding_strategy(self, numberbidders, wincondition, artists, values, rd, itemsinauction, winnerarray, winneramount, mybidderid, players, standings, winnerpays):
        """Game 3: Highest total value wins, highest bidder pays own bid, auction order known."""

        items_sold = itemsinauction[:rd]
        max_value = 0
        for art in artists.keys():
            max_value += (artists[art]-items_sold.count(art))*values[art] #this is the maximum posible value for all the paitings
        prop_d = {}
        for art in artists.keys():
            prop_d[art] = (standings[mybidderid]['money']/max(max_value,1))*values[art] #here is my valuation that distributes my budget between the maximun value relatively to the valu of the artist
        players_value = {}
        for art in artists.keys():
            players_value[art] = 0
        if rd > 0:
            for i in range(rd):
                players_value[itemsinauction[i]] = winneramount[i]
            for i in range(rd):
                if winnerarray[i] == mybidderid and winneramount[i] == players_value[itemsinauction[i]] and itemsinauction[i] == 'Da_Vinci':
                    players_value[itemsinauction[i]] = players_value[itemsinauction[i]]*0.80 #if I was the last winner of a Da Vinci I reduce the bid for 10 money
                if winnerarray[i] == mybidderid and winneramount[i] == players_value[itemsinauction[i]] and itemsinauction[i] == 'Rembrandt':
                    players_value[itemsinauction[i]] = players_value[itemsinauction[i]]*0.85 #if I was the last winner of a Rembrant I reduce the bid for 10 money
                if winnerarray[i] == mybidderid and winneramount[i] == players_value[itemsinauction[i]] and itemsinauction[i] == 'Van_Gogh':
                    players_value[itemsinauction[i]] = players_value[itemsinauction[i]]*0.90 #if I was the last winner of a Van Gogh I reduce the bid for 10 money
                if winnerarray[i] == mybidderid and winneramount[i] == players_value[itemsinauction[i]] and itemsinauction[i] == 'Picasso':
                    players_value[itemsinauction[i]] = players_value[itemsinauction[i]]*0.95 #if I was the last winner of a Picasso I reduce the bid for 10 money
                elif winnerarray[i] != mybidderid and winneramount[i] > players_value[itemsinauction[i]]:
                    players_value[itemsinauction[i]] = winneramount[i]+1 #If I am not the last winner then I bid the last payed price plus one
        if artists['Da_Vinci']-items_sold.count('Da_Vinci') == 1 and itemsinauction[rd] == 'Da_Vinci': #I bid all my money for the last Da Vinci
            return int(standings[mybidderid]['money'])
        if rd == (sum(artists.values())-1): #No matter what I return my full budget for the last painting
            return int(standings[mybidderid]['money'])
        for art in artists.keys():
            if itemsinauction[rd] == art:
                if standings[mybidderid]['money'] > 500: #the agresive strategy to bid the last price plus one is just in case I have ore than the half of my money and if the artist is a Da Vinci or a Rembrant
                    if itemsinauction[rd] == 'Picasso' or itemsinauction[rd] == 'Van_Gogh':
                        return max(int(prop_d[art]),0)
                    else:
                        return max(int(prop_d[art]),int(players_value[art]),0)
                elif standings[mybidderid]['money'] <= 500: #in case I have less than half of my money I just bid my valuation of the paint
                    return max(int(prop_d[art]),0)
                else:
                    return 0

    def fourth_bidding_strategy(self, numberbidders, wincondition, artists, values, rd, itemsinauction, winnerarray, winneramount, mybidderid, players, standings, winnerpays):
        """Game 4: Highest total value wins, highest bidder pays second highest bid, auction order known."""

        items_sold = itemsinauction[:rd]
        max_value = 0
        for art in artists.keys():
            max_value += (artists[art]-items_sold.count(art))*values[art] #again I am calculating the maximun posible value
        prop_d = {}
        for art in artists.keys():
            prop_d[art] = (standings[mybidderid]['money']/max(max_value,1))*values[art] #this is the valuation for each artist considering the maximum posible, my budget and the value of the piece
        players_value = {}
        for art in artists.keys():
            players_value[art] = 0
        if rd > 0:
            for i in range(rd):
                players_value[itemsinauction[i]] = winneramount[i]
            for i in range(rd):
                if winnerarray[i] == mybidderid and winneramount[i] > prop_d[itemsinauction[i]]:
                    players_value[itemsinauction[i]] = winneramount[i]*1.1 #if I am the winner I bid 10% more than what I payed
                elif winnerarray[i] != mybidderid:
                    players_value[itemsinauction[i]] = winneramount[i]*2 #if I am not the winner then I increase the bid to 2 times what the winner payed
        if artists['Da_Vinci']-items_sold.count('Da_Vinci') == 1 and itemsinauction[rd] == 'Da_Vinci': #I bid all my money for the last Da Vinci
            return int(standings[mybidderid]['money'])
        if rd == (sum(artists.values())-1): #No matter what I return my full budget for the last painting
            return int(standings[mybidderid]['money'])
        for art in artists.keys():
            if itemsinauction[rd] == art:
                if standings[mybidderid]['money'] > 500: #if I have more than half my budget then I mantain an aggresive strategy for the high valuable artists
                    if itemsinauction[rd] == 'Picasso' or itemsinauction[rd] == 'Van_Gogh':
                        bid = max(int(prop_d[art]*3),0) #for the less valuable artist I return 3 times my valuation
                        return bid
                    else:
                        bid = max(int(prop_d[art]),int(players_value[art]),0) #for the high valuable artists I go for the previous winner valuation
                        return bid
                elif standings[mybidderid]['money'] <= 500: #in case I have less than the half of my budget I return 3 times my valuation
                    bid = max(int(prop_d[art]*3),0)
                    return bid
                else:
                    bid = 0
                    return bid
