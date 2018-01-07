#!/usr/bin/env python
#-*- coding:utf-8 -*-

from decimal import *
import json
import re
import logging
import sqlite3
import string
import logging.config
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from tweepy.streaming import StreamListener, Stream
from tweepy.auth import OAuthHandler
from tweepy.api import API
import datetime
import time
import random

# bitcoind
rpc_user='zenyuser'
rpc_password='passwordzeny'
zeny = AuthServiceProxy("http://%s:%s@localhost:9252"%(rpc_user, rpc_password))

# logger
logging.config.fileConfig('logging.conf')
logger = logging.getLogger()

lasttime = datetime.datetime.now()

# http://d.hatena.ne.jp/karasuyamatengu/20120408/1333862237
class DotAccessible(object):
    def __init__(self, obj):
        self.obj=obj

    def __repr__(self):
        return "DotAccessible(%s)" % repr(self.obj)

    def __getitem__(self, i):
        return self.wrap(self.obj[i])

    def __getslice__(self, i, j):
        return map(self.wrap, self.obj.__getslice__(i,j))

    def __getattr__(self, key):
        if isinstance(self.obj, dict):
            try:
                v=self.obj[key]
            except KeyError:
                v=self.obj.__getattribute__(key)
        else:
            v=self.obj.__getattribute__(key)

        return self.wrap(v)

    def wrap(self, v):
        """要素をラップするためのヘルパー"""

        if isinstance(v, (dict,list,tuple)): # xx add set
            return self.__class__(v)
        return v


def get_oauth():
    consumer_key = ''
    consumer_secret = ''
    access_key = ''
    access_secret = ''
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    return auth

def DecimaltoStr(d):
	return '{0:f}'.format(d)

def str_isfloat(str):
	try:
		float(str)
		return True
 
	except ValueError:
		return False

def add_rainlist(user):
	con = sqlite3.connect('rainlist.db')
	c = con.cursor()

	create_table = '''CREATE TABLE IF NOT EXISTS rainlist(account int, name text)'''
	c.execute(create_table)

	if in_rainlist(user):
		return
	
	ins = 'insert into rainlist (account, name) values (?,?)'
	tip = (user.id, user.screen_name)
	c.execute(ins, tip)
	con.commit()
	con.close()

def get_rainlist(item):
	con = sqlite3.connect('rainlist.db')
	c = con.cursor()
	rainlist = []
	tos = c.execute("select * from rainlist")
	for row in tos:
		rainlist.append(row[item])
	con.commit()
	con.close()
	return rainlist

def in_rainlist(user):
	if user.id in get_rainlist(0):
		return True
	return False

def delete_rainlist(user):
	if in_rainlist(user):
		con = sqlite3.connect('rainlist.db')
		c = con.cursor()
		c.execute("delete from rainlist where account = ?",(user.id,))
		con.commit()
		con.close()

def savetip(from_id, to_id, amount):
	con = sqlite3.connect('tipzeny.db')
	c = con.cursor()

	create_table = '''CREATE TABLE IF NOT EXISTS tiplist(from_id int, to_id int, amount text, date_time text)'''
	c.execute(create_table)

	date_str = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
	amount = str(amount)

	ins = 'insert into tiplist (from_id, to_id, amount, date_time) values (?,?,?,?)'
	tip = (from_id, to_id, amount, date_str)
	c.execute(ins, tip)
	con.commit()
	con.close()

def gettip(user_id):
	con = sqlite3.connect('tipzeny.db')
	c = con.cursor()

	from_ids = c.execute("select * from tiplist where from_id = ?",(user_id,))
	for row in from_ids:
		date = datetime.datetime.strptime(row[3], "%Y/%m/%d %H:%M:%S")
		if datetime.datetime.now() > date + datetime.timedelta(days = 3):
			zeny.move("tippot", "tipzeny-" + str(row[0]), float(row[2]))
			c.execute("delete from tiplist where date_time = ? and from_id = ?", (row[3],row[0]))
	con.commit()

	tos = c.execute("select * from tiplist where to_id = ?",(user_id,))
	for row in tos:
		date = datetime.datetime.strptime(row[3], "%Y/%m/%d %H:%M:%S")
		if datetime.datetime.now() < date + datetime.timedelta(days = 3):
			zeny.move("tippot", "tipzeny-" + str(row[1]), float(row[2]))
			c.execute("delete from tiplist where date_time = ? and from_id = ?", (row[3],row[0]))
	con.commit()
	con.close()

def replyMessage(status,txt,istweet):
	try:
		global lasttime
		nowtime = datetime.datetime.now()
		if lasttime + datetime.timedelta(seconds = 2) > nowtime:
			lasttime = nowtime
			time.sleep(random.randint(3,5))
			replyMessage(status,txt,istweet)
			return
		text = txt + u"\n\n"
		random_str = ''.join([random.choice(string.ascii_letters + string.digits) for i in range(4)])
		text += random_str
		if istweet:
			api.update_status(status=text, in_reply_to_status_id=status.id)
		else:
			api.send_direct_message(user_id = status.user.id, text = text)
	except Exception as e:
		print(e)
		time.sleep(random.randint(30,40))
		replyMessage(status,txt,istweet)

def helptweet(status,txt,istweet):
		tweet = "@" + status.user.screen_name + u" " + txt
		replyMessage(status,tweet,istweet)

def giveme(status):
	name = status.user.screen_name
	userid = status.user.id

	if status.source.count("iPhone") == 0 and status.source.count("Android") == 0 and status.source.count("TweetDeck") == 0 and status.source.count("Web Client") == 0 and status.source.count("Mac") == 0 and status.source.count("MateCha") == 0 and status.source.count("iPad") == 0:
		tweet = "@" + name + u" You can not use it from this client:("
		replyMessage(status,tweet,True)
		return False
	if status.user.statuses_count < 100:
		tweet = "@" + name + u" Your tweets are low!"
		replyMessage(status,tweet,True)
		return False
	if status.user.created_at + datetime.timedelta(days=14) > datetime.datetime.now():
		tweet = "@" + name + u" Sorry, but I can't give you because your account does not aged 2 weeks or more."
		replyMessage(status,tweet,True)
		return False

	account = "tipzeny-" + str(userid)
	user_balance = zeny.getbalance(account,0)

	if user_balance > 10:
		tweet = "@" + name + u" Sorry, but I can't give you because your balance is 10 ZNY or more."
		replyMessage(status,tweet,True)
		return False

	pot_balance = zeny.getbalance("giveme",0)
	if pot_balance < 2:
		tweet = "@" + name + u" Sorry, I can't give you because the pool is empty. I will be happier if you can donate for it ;)"
		replyMessage(status,tweet,True)
		return False

	con = sqlite3.connect('giveme.db')
	c = con.cursor()
	create_table = '''CREATE TABLE IF NOT EXISTS faucets(user_id int primary key, dinial int, date_time text)'''
	c.execute(create_table)
	con.commit()

	date_str = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")

	c.execute("select * from faucets where user_id = ?",(userid,))
	data = c.fetchone()
	if data:
		date = datetime.datetime.strptime(data[2], "%Y/%m/%d %H:%M:%S")
		if datetime.datetime.now() < date + datetime.timedelta(days = data[1]):
			if data[1] == 1:
				tweet = "@" + name + u" Hey, you can't receive again in 24 hours."
			else:
				tweet = "@" + name + u" Hey, you can't receive from 7 days from the last withdrawals."
			replyMessage(status,tweet,True)
			con.close()
			return False
			
	logger.info("giveme..."+name)

	ins = 'replace into faucets (user_id, dinial, date_time) values (?,?,?)'
	tip = (userid, 1, date_str)
	c.execute(ins, tip)
	con.commit()
	con.close()

	amount = (50.0 + random.randint(1,50))/100
	zeny.move("giveme", account, amount)
	tweet = "@" + name + u" I give you " + str(amount) + u" ZNY to " + name + u"."
	replyMessage(status,tweet,True)
	logger.info("->"+str(amount)+"ZNY give")
	return False

def stopgiveme(userid, days):
	date_str = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
	con = sqlite3.connect('giveme.db')
	c = con.cursor()
	ins = 'replace into faucets (user_id, dinial, date_time) values (?,?,?)'
	tip = (userid, days, date_str)
	c.execute(ins, tip)
	con.commit()
	con.close()
	
# ツイート処理
def on_tweet(status, istweet):
	text = status.text
	name = status.user.screen_name
	user_id = status.user.id

	if text.find("RT") == -1 and text.find("QT") == -1 and name != "rintips":
		account = "tipzeny-" + str(user_id)
		message = ""
		text = re.sub('\n', ' ', text)

		if istweet:
			fst = text.find("@rintips")
			if fst != -1:
				message = text[fst+9:]
				if re.match("@rintips", message):
					message = message[9:]
			else:
				return
		else:
			if re.match("@rintips", text):
				message = text[9:]
			else:
				message = text

		if message is None:
			return

		if re.search("balance", message) or re.search(u"残高", message):
			gettip(user_id)
			balance = zeny.getbalance(account,6)
			all_balance = zeny.getbalance(account,0)

			if all_balance < 5:
				delete_rainlist(status.user)
			else:
				add_rainlist(status.user)

			logger.info("check balance..." + name)
			logger.info(DecimaltoStr(balance) + "ZNY all(" + DecimaltoStr(all_balance) + "ZNY)")
			tweet = "@" + name + " You have " + DecimaltoStr(balance) + u"ZNY!"
			if balance < all_balance:
				tweet += u"\n(confirm中" + DecimaltoStr(all_balance-balance) + u"ZNY)"
			replyMessage(status,tweet,istweet)

		elif not istweet and re.search(u"rainlist", message):
			try:
				logger.info("get rainlist..." + name)
				rainlist = get_rainlist(0)
				nmb = len(rainlist)
				if nmb == 0:
					tweet = "@" + name + u" 対象者がいないみたいです。。。"
					replyMessage(status,tweet,istweet)
					return

				tweet = ""
				for userid in rainlist:
					tweet += "@" + api.get_user(userid).screen_name + " \n"
				replyMessage(status,tweet,istweet)
				logger.info("-> get")
			except:
				tweet = "@" + name + u" API制限です...しばらくこのコマンドは使えません><"
				replyMessage(status,tweet,istweet)

		elif not istweet and re.search(u"rainfollowerlist", message):
			try:
				logger.info("get rainfollowerlist..." + name)
				rainlist = get_rainlist(0)
				rainfollower = []
				for userid in rainlist:
					if api.show_friendship(source_id =user_id, target_id=userid)[0].followed_by:
						rainfollower.append(userid)

				nmb = len(rainfollower)
				if nmb == 0:
					tweet = "@" + name + u" 対象者がいないみたいです。。。"
					replyMessage(status,tweet,istweet)
					return
				tweet = ""

				for followerid in rainfollower:
					tweet += "@" + api.get_user(followerid).screen_name + " \n"
				replyMessage(status,tweet,istweet)
				logger.info("-> get")
			except:
				tweet = "@" + name + u" API制限です...しばらくこのコマンドは使えません><"
				replyMessage(status,tweet,istweet)


		elif re.search("deposit", message) or re.search(u"入金", message):
			address = zeny.getaccountaddress(account)
			logger.info("get deposit address..." + name)
			logger.info(account + " => " + address)
			tweet = "@" + name + " " + address + u" に送金お願いしますっ！"
			replyMessage(status,tweet,istweet)

		elif re.match("withdrawall", message) or re.match(u"全額出金", message):
			m = re.split(" ", message)
			if len(m) < 2:
				helptweet(status, u"withdrawall \n@￰rintips withdrawall address\nhttps://github.com/trasta298/tipzeny/wiki",istweet)
				return

			address = m[1]
			balance = zeny.getbalance(account,6)
			tax = 0.01
			payying = float(balance)-tax

			logger.info("withdraw..."+name)

			if round(0-payying,7) >= 0:
				logger.info("-> Not enough ZNY (0.01 > " + str(payying) + ")")
				tweet = "@" + name + u" 残高が足りないみたいですっ！\n所持zny: " + str(balance) + "ZNY"
				replyMessage(status,tweet,istweet)
				return

			validate = zeny.validateaddress(address)
			if not validate['isvalid']:
				logger.info("-> Invalid address")
				tweet = "@" + name + u" アドレスが間違ってるみたいですっ"
				replyMessage(status,tweet,istweet)
				return

			logger.info("-> Sending...")
			txid = zeny.sendfrom(account,address,payying)

			# taxまわりとりあえず後回し
			logger.info("-> Checking transaction...")
			tx = zeny.gettransaction(txid)
			if tx:
				fee = float(tx['fee'])
				logger.info("-> Tax: " + str(fee))
			else:
				fee = 0
				logger.info("-> No Tax")

			zeny.move(account, "taxpot", tax+fee)
			logger.info("-> Fee sent to taxpot: " + str(tax+fee) + "ZNY")
			tweet = "@" + name + u" zenyを引き出しましたっ！(手数料0.01ZNY)\nhttp://namuyan.dip.jp/MultiLightBlockExplorer/gettxid.php?coin=zeny&txid=" + str(txid)
			replyMessage(status,tweet,istweet)

			stopgiveme(user_id, 7)

			delete_rainlist(status.user)

		elif re.match("withdraw", message) or re.match(u"出金", message):
			m = re.split(" ", message)
			if len(m) < 3 or not str_isfloat(m[2]):
				helptweet(status, u"withdraw(出金)の使い方\n@￰rintips withdraw 受取ZNYアドレス 出金額(ZNY)\nhttps://github.com/trasta298/tipzeny/wiki",istweet)
				return

			address = m[1]
			amot= float(m[2])
			balance = zeny.getbalance(account,6)
			tax = 0.01
			amount = amot-tax

			if amount <= 0:
				tweet = "@" + name + u" 0以下の数は指定できません！"
				replyMessage(status,tweet,istweet)
				return

			logger.info("withdraw..."+name)

			if round(Decimal(amount)-balance,7) >= 0:
				logger.info("-> Not enough ZNY ("+ DecimaltoStr(balance) + " < " + str(amount) + ")")
				tweet = "@" + name + u" 残高が足りないみたいですっ！\n所持zny: " + DecimaltoStr(balance) + "ZNY"
				replyMessage(status,tweet,istweet)
				return

			validate = zeny.validateaddress(address)
			if not validate['isvalid']:
				logger.info("-> Invalid address")
				tweet = "@" + name + u" アドレスが間違ってるみたいですっ"
				replyMessage(status,tweet,istweet)
				return

			logger.info("-> Sending...")
			txid = zeny.sendfrom(account,address,amount)

			# taxまわりとりあえず後回し
			logger.info("-> Checking transaction...")
			tx = zeny.gettransaction(txid)
			if tx:
				fee = float(tx['fee'])
				logger.info("-> Tax: " + str(fee))
			else:
				fee = 0
				logger.info("-> No Tax")

			zeny.move(account, "taxpot", tax+fee)
			logger.info("-> Fee sent to taxpot: " + str(tax+fee) + "ZNY")
			tweet = "@" + name + u" zenyを引き出しましたっ！(手数料0.01ZNY)\nhttp://namuyan.dip.jp/MultiLightBlockExplorer/gettxid.php?coin=zeny&txid=" + str(txid)
			replyMessage(status,tweet,istweet)

			stopgiveme(user_id, 7)

			if float(balance)-amount < 5:
				delete_rainlist(status.user)

		elif re.match("rainfollower", message):
			try:
				m = re.split(" ", message)
				if len(m) < 2 or not str_isfloat(m[1]):
					helptweet(status, u"rainfollowerの使い方\n@￰rintips rainfollower 撒銭額(ZNY)\nhttps://github.com/trasta298/tipzeny/wiki",istweet)
					return
				amount = float(m[1])
				balance = zeny.getbalance(account,6)

				if amount < 0.01:
					tweet = "@" + name + u" 0.01より小さい数は指定できません！"
					replyMessage(status,tweet,istweet)
					return

				logger.info("RainingFollower..."+str(amount)+"ZNY from "+name)

				if round(Decimal(amount)-balance,7) > 0:
					logger.info("-> Not enough ZNY ("+ DecimaltoStr(balance) + " < " + str(amount) + ")")
					tweet = "@" + name + u" 残高が足りないみたいですっ！\n所持zny: " + DecimaltoStr(balance) + "ZNY"
					replyMessage(status,tweet,istweet)
					return

				rainlist = get_rainlist(0)
				if len(rainlist) == 0:
					tweet = "@" + name + u" 対象者がいないみたいです。。。"
					replyMessage(status,tweet,istweet)
					return

				rainfollower = []
				for userid in rainlist:
					if api.show_friendship(source_id =user_id, target_id=userid)[0].followed_by:
						rainfollower.append(userid)

				nmb = len(rainfollower)
				if nmb == 0:
					tweet = "@" + name + u" 対象者がいないみたいです。。。"
					replyMessage(status,tweet,istweet)
					return
				mon = round(amount/nmb,7)

				for followerid in rainfollower:
					to_account = "tipzeny-" + str(followerid)
					zeny.move(account,to_account,mon)

				logger.info("-> Sent.")

				tweet = "@" + name + u" " + str(nmb) + u"人にそれぞれ @" + name + u" さんより" + str(mon) + u"ZNYずつ送りましたっ！"
				replyMessage(status,tweet,istweet)
			except:
				tweet = "@" + name + u" API制限です...しばらくこのコマンドは使えません><"
				replyMessage(status,tweet,istweet)


		elif re.match("rain", message) or re.match(u"撒き銭", message):
			try:
				m = re.split(" ", message)
				if len(m) < 2 or not str_isfloat(m[1]):
					helptweet(status, u"rain(撒き銭)の使い方\n@￰rintips rain 撒銭額(ZNY)\nhttps://github.com/trasta298/tipzeny/wiki",istweet)
					return
				amount = float(m[1])
				balance = zeny.getbalance(account,6)

				if amount < 0.01:
					tweet = "@" + name + u" 0.01より小さい数は指定できません！"
					replyMessage(status,tweet,istweet)
					return

				logger.info("Raining..."+str(amount)+"ZNY from "+name)

				if round(Decimal(amount)-balance,7) > 0:
					logger.info("-> Not enough ZNY ("+ DecimaltoStr(balance) + " < " + str(amount) + ")")
					tweet = "@" + name + u" 残高が足りないみたいですっ！\n所持zny: " + DecimaltoStr(balance) + "ZNY"
					replyMessage(status,tweet,istweet)
					return

				rainlist = get_rainlist(0)
				nmb = len(rainlist)
				if nmb == 0:
					tweet = "@" + name + u" 対象者がいないみたいです。。。"
					replyMessage(status,tweet,istweet)
					return

				mon = round(amount/nmb,7)
				for userid in rainlist:
					to_account = "tipzeny-" + str(userid)
					zeny.move(account,to_account,mon)
				logger.info("-> Sent.")

				tweet = "@" + name + u" " + str(nmb) + u"人にそれぞれ @" + name + u" さんより" + str(mon) + u"ZNYずつ送りましたっ！"
				replyMessage(status,tweet,istweet)
			except:
				tweet = "@" + name + u" API制限です...しばらくこのコマンドは使えません><"
				replyMessage(status,tweet,istweet)

		elif re.match("send", message) or re.match(u"送金", message):
			m = re.split(" ", message)
			if len(m) < 3 or not str_isfloat(m[2]):
				helptweet(status, u"send(送金)の使い方\n@￰rintips send @￰twitterアカウント 投銭額(ZNY)\nhttps://github.com/trasta298/tipzeny/wiki",istweet)
				return
			if m[1][0] != "@":
				helptweet(status, u"send(送金)の使い方\n@￰rintips send @￰twitterアカウント 投銭額(ZNY)\nhttps://github.com/trasta298/tipzeny/wiki",istweet)
				return

			to = m[1][1:]
			amount = float(m[2])
			balance = zeny.getbalance(account,6)

			if amount <= 0:
				tweet = "@" + name + u" 0以下の数は指定できません！"
				replyMessage(status,tweet,istweet)
				return

			logger.info("Sending..."+str(amount)+"ZNY from "+name+" to "+to)

			if round(Decimal(amount)-balance,7) > 0:
				logger.info("-> Not enough ZNY ("+ DecimaltoStr(balance) + " < " + str(amount) + ")")
				tweet = "@" + name + u" 残高が足りないみたいですっ！\n所持zny: " + DecimaltoStr(balance) + "ZNY"
				replyMessage(status,tweet,istweet)
				return

			try:
				to_user = api.get_user(to)

			except:
				logger.info("-> User not found.")
				tweet = "@" + name + u" 送り主(" + to + u")が見つかりませんでした…"
				replyMessage(status,tweet,istweet)
				return

			to_account = "tipzeny-" + str(to_user.id)
			zeny.move(account,to_account,amount)
			logger.info("-> Sent.")
			tweet = "@" + to + u" りん姫より @" + name + u" さんから" + str(amount) + u"ZNYのお届け物だよっ！"
			replyMessage(status,tweet,istweet)

		elif re.match("tip", message) or re.match(u"投銭", message):
			m = re.split(" ", message)
			if len(m) < 3 or not str_isfloat(m[2]):
				helptweet(status, u"tip(投銭)の使い方\n@￰rintips tip @￰twitterアカウント 投銭額(ZNY)\nhttps://github.com/trasta298/tipzeny/wiki",istweet)
				return
			if m[1][0] != "@":
				helptweet(status, u"tip(投銭)の使い方\n@￰rintips tip @￰twitterアカウント 投銭額(ZNY)\nhttps://github.com/trasta298/tipzeny/wiki",istweet)
				return

			to = m[1][1:]
			amount = float(m[2])
			balance = zeny.getbalance(account,6)

			if amount <= 0:
				tweet = "@" + name + u" 0以下の数は指定できません！"
				replyMessage(status,tweet,istweet)
				return

			logger.info("Tip..."+str(amount)+"ZNY from "+name+" to "+to)

			if round(Decimal(amount)-balance,7) > 0:
				logger.info("-> Not enough ZNY ("+ DecimaltoStr(balance) + " < " + str(amount) + ")")
				tweet = "@" + name + u" 残高が足りないみたいですっ！\n所持zny: " + DecimaltoStr(balance) + "ZNY"
				replyMessage(status,tweet,istweet)
				return

			try:
				to_user = api.get_user(to)

			except:
				logger.info("-> User not found.")
				tweet = "@" + name + u" 送り主(" + to + u")が見つかりませんでした…"
				replyMessage(status,tweet,istweet)
				return

			to_account = "tipzeny-" + str(to_user.id)

			if re.match("rintips",to):
				zeny.move(account,"giveme",amount) #tipzeny-3029861817
				logger.info("-> Sent.")
				tweet = "@" + to + u" りん姫より @" + name + u" さんから" + str(amount) + u"ZNYの寄付だよっ！ありがとっ！givemeやサーバー維持費に使わせてもらうね！"
				replyMessage(status,tweet,istweet)
				return

			savetip(user_id, to_user.id, amount)
			zeny.move(account,"tippot",amount)
			logger.info("-> Sent.")
			tweet = "@" + to + u" りん姫より @" + name + u" さんから" + str(amount) + u"ZNYのお届け物だよっ！ 3日以内にbalanceして受け取ってね！"
			replyMessage(status,tweet,istweet)

		elif re.match("otoshidama", message) or re.match(u"お年玉", message):
			today = datetime.datetime.now() + datetime.timedelta(hours=9)
			if today.day != 1 or today.month != 1:
				tweet = "@" + name + u" 今日はお正月じゃないよっ！"
				replyMessage(status,tweet,istweet)
				return
			m = re.split(" ", message)
			if len(m) < 3 or not str_isfloat(m[2]):
				helptweet(status, u"otoshidama(お年玉)の使い方\n@￰rintips お年玉 @￰twitterアカウント 投銭額(ZNY)\nhttps://github.com/trasta298/tipzeny/wiki",istweet)
				return
			if m[1][0] != "@":
				helptweet(status, u"otoshidama(お年玉)の使い方\n@￰rintips お年玉 @￰twitterアカウント 投銭額(ZNY)\nhttps://github.com/trasta298/tipzeny/wiki",istweet)
				return

			to = m[1][1:]
			amount = float(m[2])
			balance = zeny.getbalance(account,6)

			if amount <= 0:
				tweet = "@" + name + u" 0以下の数は指定できません！"
				replyMessage(status,tweet,istweet)
				return

			logger.info("Tip..."+str(amount)+"ZNY from "+name+" to "+to)

			if round(Decimal(amount)-balance,7) > 0:
				logger.info("-> Not enough ZNY ("+ DecimaltoStr(balance) + " < " + str(amount) + ")")
				tweet = "@" + name + u" 残高が足りないみたいですっ！\n所持zny: " + DecimaltoStr(balance) + "ZNY"
				replyMessage(status,tweet,istweet)
				return

			try:
				to_user = api.get_user(to)

			except:
				logger.info("-> User not found.")
				tweet = "@" + name + u" 送り主(" + to + u")が見つかりませんでした…"
				replyMessage(status,tweet,istweet)
				return

			to_account = "tipzeny-" + str(to_user.id)

			if re.match("tra_sta",to) or re.match("rintips",to):
				zeny.move(account,"tipzeny-3029861817",amount)
				logger.info("-> Sent.")
				tweet = "@" + to + u" りん姫より @" + name + u" さんから" + str(amount) + u"ZNYのお年玉だよっ！ あけましておめでとう！今年もよろしくねっ！"
				replyMessage(status,tweet,istweet)
				return

			savetip(user_id, to_user.id, amount)
			zeny.move(account,"tippot",amount)
			logger.info("-> Sent.")
			tweet = "@" + to + u" りん姫より @" + name + u" さんから" + str(amount) + u"ZNYのお年玉だよっ！ あけましておめでとう！今年もよろしくねっ！ 3日以内にbalanceして受け取ってね！"
			replyMessage(status,tweet,istweet)

		elif re.match(u"osaisen", message) or re.match(u"お賽銭", message):
			today = datetime.datetime.now() + datetime.timedelta(hours=9)
			if today.day != 1 or today.month != 1:
				tweet = "@" + name + u" 今日はお正月じゃないよっ！"
				replyMessage(status,tweet,istweet)
				return
			m = re.split(" ", message)
			if len(m) < 2 or not str_isfloat(m[1]):
				helptweet(status, u"osaisen(お賽銭)の使い方\n@￰rintips お賽銭 投銭額(ZNY)\nhttps://github.com/trasta298/tipzeny/wiki",istweet)
				return

			amount = float(m[1])
			balance = zeny.getbalance(account,6)

			if amount <= 0:
				tweet = "@" + name + u" 0以下の数は指定できません！"
				replyMessage(status,tweet,istweet)
				return

			logger.info("Saisen..."+str(amount)+"ZNY from "+name+" to trasta")

			if round(Decimal(amount)-balance,7) > 0:
				logger.info("-> Not enough ZNY ("+ DecimaltoStr(balance) + " < " + str(amount) + ")")
				tweet = "@" + name + u" 残高が足りないみたいですっ！\n所持zny: " + DecimaltoStr(balance) + "ZNY"
				replyMessage(status,tweet,istweet)
				return

			zeny.move(account,"tipzeny-3029861817",amount)
			logger.info("-> Sent.")
			tweet = "@" + name + u" お賽銭" + str(amount) + u"ZNYを投げましたっ！ 今年もいいことがありますように。。。"
			replyMessage(status,tweet,istweet)

		elif re.search("give me", message) or re.search("giveme", message):
			if istweet:
				giveme(status)

		elif re.match("help", message) or len(message) < 2:
			helptweet(status, u"りん姫の使い方はここっ\nhttps://github.com/trasta298/tipzeny/wiki",istweet)


class Listener(StreamListener):
    def on_status(self, status):
    	on_tweet(status, True)
        return True

    def on_direct_message(self, status):
    	data = status.direct_message
    	data['user'] = data['sender']
    	on_tweet(DotAccessible(data), False)
    	return True

    def on_error(self, status_code):
        logger.error('エラー発生: ' + str(status_code))
        return True

    def on_connect(self):
        logger.info('Streamに接続しました')
        return

    def on_disconnect(self, notice):
        logger.info('Streamから切断されました:' + str(notice.code))
        return

    def on_limit(self, track):
        logger.warning('受信リミットが発生しました:' + str(track))
        return

    def on_timeout(self):
        logger.info('タイムアウト')
        return True

    def on_warning(self, notice):
        logger.warning('警告メッセージ:' + str(notice.message))
        return

    def on_exception(self, exception):
        logger.error('例外エラー:' + str(exception))
        return True


# main
if __name__ == '__main__':
    auth = get_oauth()
    api = API(auth)
    stream = Stream(auth, Listener(), secure=True)
    stream.userstream()
