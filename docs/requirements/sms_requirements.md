# SMS requirements

These are the requirements for the finished text-message channel. Each item must hold. If one item does not happen, the channel does not work.

The person can ask in their own words. The channel can do five things: give the balance, give the PIN, give a statement, block the card, and unblock the card. It does not do anything else.

1. The channel is available every day, at every hour.
2. The number they text is the same number they would call.
3. One conversation is a series of messages. The system can ask a question, and the next message answers it. A new message that is not answering the system starts a new conversation.
4. A message with no words gets no reply. A picture with no caption gets no reply. A caption is treated as the words of the message.
5. A number that is not a customer's number is refused. The reply says the number is not recognised. The system does not ask for card digits and does not give any account information.
6. Every reply is in the language of the message it is answering, including a refusal, a question, and a result. The language of an earlier message in the same conversation does not change this reply.
7. Before any balance, PIN, statement, block, or unblock, the person must give the last 4 digits of the card. The system asks once per conversation. A later request in the same conversation does not ask again.
8. If their first message already asks for an action, the system asks for the last 4 first. It does not give the result until the digits are correct. After the digits are correct, it carries out the request they already made.
9. A wrong last 4 gives no account information and makes no change to the card. They may try once more in the same conversation. A second wrong last 4 ends the conversation.
10. If the person has one card, the system uses that card and does not ask which card it is.
11. If the person has more than one card, the system asks which card before it acts, unless the person has already identified one. They may name the card or give its last 4 digits. A last 4 that matches one of their cards both chooses that card and satisfies the check. A last 4 that matches none of their cards is a wrong last 4.
12. After the check has passed, the person can make several requests in the same conversation, in their own words. They can correct a request that has not yet been carried out. A correction replaces the pending request. It is not counted as a misunderstood request.
13. If they ask for more than one of the five actions in one message, the system handles them one at a time, in the order they asked. It finishes or confirms one before it starts the next. The next message can be the confirmation.
14. The system does not guess. A request it does not understand, or a request that is not one of the five actions, is declined. The reply names the five things it can do: balance, PIN, statement, block, and unblock. They get two such failures, then the conversation ends. The ending reply names those five things and does not ask another question.
15. A balance reply contains the amount, the currency, and the date and time that amount is true for. The amount is the real balance of the chosen card. Balance does not wait for a yes.
16. A PIN reply contains the real PIN of the chosen card. It contains no other card's PIN. The PIN does not wait for a yes. A later message does not include the PIN again unless they ask for it again.
17. A statement reply contains the statement period and the closing balance for that period. It does not have to list every transaction. If they name a period, that period is used. If they do not name a period, the latest statement is used, and the reply says which period it is. If they name a period that has no statement, the system says so and asks for another period. That question is not a misunderstood request. A statement does not wait for a yes.
18. Block and unblock change the card. The system asks for a clear yes before it changes anything. The next message answers that question. A clear no cancels the change. The card stays as it was, and they can ask for something else.
19. An unclear answer to yes or no asks the same question once more. A second unclear answer cancels the change. The card is not changed. This does not count as one of the two misunderstood requests.
20. After a yes, a block leaves the card blocked, and the person is told that it is blocked. An unblock leaves the card unblocked, and the person is told that it is unblocked. The change is real.
21. If the card is already blocked, the system says so and does not ask for a yes to block it again. If the card is already unblocked, the system says so and does not ask for a yes to unblock it again.
22. Until they say yes, they can replace a pending block or unblock with a different request. The cancelled change does not happen.
23. Sending the same request again as a new conversation asks for the last 4 again before it gives any account information.
