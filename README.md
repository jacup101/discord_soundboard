# Discord Soundboard
A Discord bot that acts as a soundboard for your server :)
**Note: This bot is very much work in progress, please excuse poor code habits as I clean it up :)**

# Features:
- Bot will join and play designated sound based on emote, including default and server emotes
- Bot reacts to both the use of emote in chat, as well as reactions
- Implementation of a queue system to queue up sounds (although, depending on the sounds, this might not be recommended 😅)
- Bot either joins voice channel of user who called it, or joins voice channel with most members if user is not in VC

# WIP
- Music Bot: Create a local library of music and play using discord slash commands

# To be implemented
- Bot currently can only read one emote from a message, can make it read all now that the queue is in place
- Clean up code 😅
- Stop being lazy and write the simple code to load token from ENV
- Add more emote examples here

# Use
- To add an emote, simply add a JSON object to the list array in emote_to_mp3.json, as shown below:
- (Note: if the emote is custom, then the name must be equal to the emote's actual name for reactions to work properly)
{
  "list":
  [
    {
      "name": "giraffle",
      "emote": "<:giraffle:927087317137637387>",
      "audio": "giraffe.mp3",
      "limit": 25,
      "image": "null",
      "is_custom": "yes",
      "is_singular": "yes",
      "is_random": "no",
      "random": [],
      "description": "Giraffe"
    }
  ]
}
