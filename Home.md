# Usages for Rinhime(りん姫), the BitZeny tipping bot on Twitter

This is the help page for Rinhime, the BitZeny tipping bot on Twitter. Please refer below for commands.    
You can use any command except for `giveme` command.    
For any issues about the bot (stopped, or bugs), please contact the dev's [Twitter](https://twitter.com/tra_sta).    
    
Cautions:
- Follow back won't be done for everyone.
- You need at least 5 ZNY for receiving RAIN.

## balance
### @zenytips balance (any comment, optional)
Replies you the balance you have.   
**Example:** `@zenytips balance`    
<img src="https://i.imgur.com/kjoqPPN.png" alt="" width="50%" height="50%">

## deposit
### @zenytips deposit (any comment, optional)
Replies you deposit address.    
**Example:** `@zenytips deposit`     
<img src="https://i.imgur.com/r6cxfFc.png" alt="" width="50%" height="50%">

## withdraw
### @zenytips withdraw (ZNY address, required) (amount to withdraw, required)
Withdraws specified amount of BitZeny to the specified address.    
**Example:** `@zenytips withdraw ZuGdQvycbE9HTfke3EPcSUQEH2joaYqXjj 10`    
<img src="https://i.imgur.com/NNqJiEu.png" alt="" width="50%" height="50%">

## withdrawall
### @zenytips withdrawall (ZNY address, required)
Withdraws *all* BitZeny to the specified address.        
**Example:** `@zenytips withdrawall ZuGdQvycbE9HTfke3EPcSUQEH2joaYqXjj`    
**CAUTION:** This command will withdraw **ALL** BitZeny including the last 5ZNY.

## send
### @￰zenytips send (Twitter account ID starting with @, required) (amount to send, required) (any comment, optional)
Sends specified amount of BitZeny to the specified account.

## tip
### @￰zenytips tip (Twitter account ID starting with @, required) (amount to tip, required) (any comment, optional)
Sends specified amount of BitZeny to the specified account.    
The receiver needs to use `balance` command within 3 days to receive.    
If the receiver didn't received your tip, it'll be sent back to your balance.    
**Example:** `@zenytips tip @tra_sta 3.9 Thanks!`
**Tips:** You can donate the author by: `@￰zenytips tip @￰zenytips (amount to tip, required)`

## rain
### @￰zenytips rain (amount to rain, required)<br>
Delivers equally ZNYs to the users who fulfilled the following condition:
- Have deposited at least 5 ZNY.

## rainlist
Only available in the Direct Messages.    
Replies the list of users who fulfilled the condition to get rained.

## rainfollower
### @￰zenytips rainfollower 撒銭額<br>
Delivers equally ZNYs to the users who fulfilled the following conditions:
- Have deposited at least 5 ZNY.
- Your follower.
**Caution:** Don't abuse this, since it is a one of heavier operations.

## rainfollowerlist
Only available in the Direct Messages.    
Replies the list of users who fulfilled the condition to get rained in your follower.

## giveme
### @zenytips giveme (コメント)<br>
以下の条件を満たしているときにちょっとだけZNYがもらえます。また、DMではこのコマンドは使えません。<br><br>
・公式クライアントを使用していること<br>
・100ツイート以上であること<br>
・アカウントを作成してから2週間以上経過していること<br>
・残高10ZNY以下であること<br>
・最後の出金から7日以上経ってること<br>
・最後のgivemeから24時間以後であること<br><br>


## A hidden command only available for the New Year Day
### @￰zenytips お年玉 @￰twitterアカウント 投銭額 (コメント)<br>
tipのところをお年玉に変えても使えるよーって話。<br>
### @￰zenytips お賽銭 投銭額 (コメント)<br>
賽銭を投げることができます。いっぱい投げるとご利益があるかも...？あと私がうれしいので是非
