# SMS requirements

These are the requirements for the finished text-message channel. Each item must hold. If one item does not happen, the channel does not work.

The person can ask in their own words. The channel can do five things: give the balance, give the PIN, give a statement, block the card, and unblock the card. It does not do anything else.

When the inbound message is English, every reply is the English sentence given below and nothing else, apart from the card lines and the values that sentence leaves room for. When the inbound message is not English, the reply is in that language, states the same facts, asks the same question if the English sentence asks one, and adds no balance, PIN, statement, or card change that the English sentence does not add.

The exact number of languages will depend on technical implementation. The list will require English, Hebrew, Yiddish, and Arabic.

## Messages that are not a conversation

1. The channel answers every day, at every hour.
2. The number they text is the same number they would call.
3. A message with no words gets no reply. It does not start a conversation, does not change what is remembered, and does not change the two-hour time. A picture with no caption is a message with no words. A caption is the words of the message.
4. One inbound message with words produces one reply. A second message, even with the same words, is a new message and produces its own reply.

## Who is refused before anything is remembered

5. The sending number is a customer only when it is the same phone number as a customer. A shorter number, a longer number, or a different number is not that customer.
6. A sending number that is not a customer gets one reply and nothing is remembered. The English reply is "This number is not recognised." The reply asks no question and contains no card digits, balance, PIN, statement, or block state. The next message from that number is refused the same way.

## What one conversation is

7. Each customer number has at most one open conversation.
8. A new message starts a new conversation when any of these is true:
    - That number has no open conversation.
    - The new message arrives two hours or more after the previous inbound message with words from that same number. A message at 10:00 and the next at 12:00 is a new conversation. A message at 11:59 is the same conversation.
    - The previous reply was an ending reply. Ending replies are the second wrong last-4 reply and the second not-understood reply. The next message is a new conversation even when it arrives one minute later.
9. A conversation that has answered a request stays open. Another request before the two hours are up does not ask for the last 4 again.

## What is remembered

10. The open conversation is remembered only for that sending number, and only inside the running service. It is not kept after the conversation ends, and a restart drops it for every number.
11. The remembered facts are only these:
    - whether the last-4 check has passed
    - the chosen card, if one has been chosen
    - the waiting actions, in order, each one of balance, PIN, statement, block, or unblock
    - the pending question, which is one of: none, last 4, which card, card name after shared digits, statement month, yes or no
    - the action the yes-or-no question is about, when that question is pending
    - the number of wrong last-4 attempts, starting at 0
    - the number of not-understood messages, starting at 0
    - the number of unclear yes-or-no answers for the current question, starting at 0
    - the time of the last inbound message with words from that number
12. The words of earlier messages are not remembered. A balance amount is not repeated in a later reply unless they ask for the balance again. A PIN is not included in a later reply unless they ask for the PIN again.
13. The not-understood count returns to 0 when an action is carried out or a yes-or-no question is asked. The wrong-last-4 count does not return to 0 until the conversation ends.

## Cards

14. A customer with no card gets one reply and nothing is remembered. The English reply is "There is no card on this number." It asks no question and contains no balance, PIN, statement, or block state.
15. A customer with one card is not asked which card it is. That card is the chosen card once the last 4 of that card has been accepted.
16. A customer with more than one card is asked which card before any action, unless the message has already selected one card. The English reply is:

    "You have more than one card. Reply with the card name or the last 4 digits."

    After that sentence, one line per card, in the form "{card name} {last 4}". The last 4 on each line are four digits with no spaces. The reply does not ask them to reply with a list number.

17. A last-4 answer is a message that contains exactly four digits after spaces and dashes are ignored. "1234", "12 34", and "12-34" are the digits 1234. "1234 please" is still the digits 1234. "12345", "1234 and 5678", and "one two three four" are not last-4 answers.
18. Four digits that match one of their cards, and no other card of theirs, select that card and pass the check.
19. Four digits that match none of their cards are a wrong attempt. They do not select a card and do not pass the check.
    - The first wrong attempt keeps the conversation open. The English reply is "Those digits do not match a card. Reply with the last 4 digits of the card." The pending question is last 4.
    - The second wrong attempt ends the conversation and forgets it. The English reply is "Those digits do not match a card. This conversation is finished." It asks no question.
20. Four digits that match more than one of their cards do not select a card, do not pass the check, and are not a wrong attempt. The English reply is "Those digits match more than one card. Reply with the card name." The following lines are the matching card names only. The pending question is card name after shared digits.
21. A card-name answer is the whole message, with spaces at the ends removed, matching one listed card name while ignoring capital letters. Extra words do not match.
22. A name that matches one listed card selects that card. If the last 4 already given match that card, the check passes. If no last 4 has been accepted for it yet, the pending question becomes last 4 and the English reply is "Reply with the last 4 digits of {card name}."
23. A name that matches more than one listed card does not select a card. The English reply is "That name matches more than one card. Reply with the last 4 digits." The pending question is last 4, and only the cards with that name are eligible for the next four digits.
24. Two cards with the same name and the same last 4 cannot be told apart. They are left off the choice list. If every card on the number is in such a pair, nothing is remembered and the English reply is "Two cards on this number cannot be told apart. No balance, PIN, statement, or change can be given." If some other card can be told apart, the choice list contains only those other cards, and the English reply adds, before the list, "Some cards on this number cannot be told apart, and those are not listed."

## How a message is read

25. A message with words from a customer is read in this order:
    - Decide whether it starts a new conversation, using items 8 and 10.
    - If a question is pending, read the message as the answer to that question.
    - If the answer selects a card or passes the check, do that, then carry out the waiting actions.
    - If no question is pending, read the message as a new request.
26. While a question is pending, a message that is a valid answer to that question is not a new request. A message that is not a valid answer is handled as follows:
    - Pending yes or no: use the yes-or-no rules below.
    - Pending last 4, which card, card name, or statement month: if the message asks for one or more of the five actions, that request replaces the waiting actions and the pending question stays until a card is selected and the check has passed. If the message does not ask for one of the five and is not a valid answer, the not-understood count increases by one and the reply repeats the pending question after the not-understood sentence.
27. A request is understood only when the message asks for one or more of the five actions. These English messages are fixed:
    - "balance", "what's my balance", and "what is my balance" are balance.
    - "PIN", "what's my PIN", and "what is my PIN" are PIN.
    - "statement" and "my statement" are statement.
    - "block my card" and "block the card" are block.
    - "unblock my card" and "unblock the card" are unblock.
    - "block my card and tell me the balance" is block, then balance.
    - "what's the weather", "hello", and "thanks" are not understood.
28. Any other message that asks for one of those five things, and not for a different one of them, is that action. A message that asks for more than one is those actions in the order the message asks for them. A message that asks for none of them is not understood.
29. The first not-understood message in the current count keeps the conversation open. The English sentence is "I can help with a balance, a PIN, a statement, blocking a card, or unblocking a card." If a question is still pending, the reply then repeats that question.
30. The second not-understood message ends the conversation and forgets it. The English reply is "I can help with a balance, a PIN, a statement, blocking a card, or unblocking a card. This conversation is finished." It asks no question.

## Carrying out an action

31. Waiting actions are carried out one at a time, in order. An action that needs no further question is included in the reply. If the next action needs a question, the reply asks that question and does not start the action after it.
32. No action is carried out until one card is selected and the last-4 check has passed. A first message that already asks for an action remembers that action and asks the next missing question. It does not give the result in that same reply unless the same message also selects the card and passes the check.
33. A balance result uses the real balance of the chosen card. The English reply is "The balance is {amount} {currency} as of {YYYY-MM-DD HH:MM} UTC." The amount is the normal decimal amount for that currency. The currency is its three-letter code. The time is 24-hour UTC. Balance does not wait for a yes.
34. A PIN result uses the real PIN of the chosen card. The English reply is "Your PIN is {PIN}." It contains no other card's PIN and no other sentence. PIN does not wait for a yes.
35. A statement result contains the period and the closing balance. It does not list transactions. The English reply is "The statement for {month} {year} closed at {amount} {currency}." The amount and currency use the same form as a balance. Statement does not wait for a yes.
    - No month named: use the most recent statement that exists for that card, and name that month and year.
    - A month and a year named: use that month.
    - A month named and no year: use the latest occurrence of that month that is not in the future.
    - No statement for that month: do not count a not-understood message. The pending question becomes statement month. The English reply is "There is no statement for {month} {year}. Reply with a month and a year."
36. Block and unblock are the only actions that wait for a yes. The English block question is "Do you want to block {card name}? Reply yes or no." The English unblock question is "Do you want to unblock {card name}? Reply yes or no."
37. The whole message, ignoring capital letters, end spaces, and one trailing full stop or exclamation mark, is a yes only when it is exactly one of these words: yes, yeah, yep, oui, ken, כן, naam, نعم, ndiyo. It is a no only when it is exactly one of these words: no, nope, non, lo, לא, la, لا, hapana. Any other message is not a yes or a no. A yes or a no contains no request.
38. Yes blocks or unblocks the chosen card for real. The English replies are "The card {card name} is blocked." and "The card {card name} is unblocked."
39. No makes no change. The English replies are "The card {card name} was not blocked." and "The card {card name} was not unblocked." The conversation stays open.
40. The first unclear answer to the same yes-or-no question does not change the card and does not increase the not-understood count. The English reply repeats "Reply yes or no." The second unclear answer cancels the change, sets the unclear count back to 0, and does not increase the not-understood count. The English reply is "The card {card name} was not changed."
41. While yes or no is pending, a message that asks for one of the five actions cancels the pending change, makes no change, and replaces the waiting actions with the actions in that message. The reply then carries out that new request. The cancelled block or unblock does not happen.
42. If the chosen card is already blocked, a block does not ask for yes. The English reply is "The card {card name} is already blocked." If it is already unblocked, an unblock does not ask for yes. The English reply is "The card {card name} is already unblocked." Any later waiting action still follows in that same reply.
