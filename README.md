# Standardized Bump Link Protocol

## Introdution

To make it easier for users to use multiple bump bots, SBLP aims to allow bumping with a single command on any compatible bump bot.

## Terminology

In the following documentation, we use "SBLP" or simply "Protocol" to refer to this protocol. The "user" is the user that used the bump command on a guild. "Bumping Bot" or "Requesting Bot" is the bot that initially received the command by the user and is now requesting the other bots to bump the server where the bump was requested on. "Receiving Bot" is the bot that received the bump requet by the bumping bot. The "guild" simply is the guild where the user executed the bump command on. The messages that are sent between the bots to communicate are either called the "request" and the "response" or just the "message payload" or "message".

## Communication

When a user bumps their server with a bump bot, the bump bot sends a message to a channel on a guild. While in most cases this will be a channel on the official SBLP guild, it can be any channel as long as other compatible bump bots are listening to messages in that channel.

The messages sent are plain text (no embeds) and formatted in JSON. To respond to a bump request, bump bots send bump response payload messages. These can be linked to the bump request using the "response" parameter in the response. It contains the Discord message ID of the original request message.

Because this type of communication uses a push technique and requires the bumping bot to await responses from recipients without actively being able to block the thread, responses can take some time and are optional. To solve this issue, we recommend having a handler class that creates a temporary object for the current bump in progress and destroys it after the bump is finished. The bot developers however can choose any solution they want, as long as it is compatible with this protocol.

### Example

Open Bump solves this with a similar solution as mentioned above: It has a SBLPBumpEntity class which keeps track of the progress and state of other bots, and a SBLP class that manages the bump entity instances. When a bump request is received (or created), it creates a new instance of the SBLPBumpEntity class and registers it in the SBLP class. The SBLP class then is able to forward incoming SBLP payloads to the corresponding bump entity using the response ID. After 60 seconds, the SBLPBumpEntity instance automatically unregisters itself from the SBLP class and marks all outstanding bumps with a timeout.

## Sharding

As communication will always be done through a channel, it will always be received on the shard with that channel on it. It is up to the receiving bot to forward the bump payload messages to the corresponding shard. We recommend using built-in solutions like Discord.js' ShardManager or Discord.py's AutoSharding.
Even though the same can apply for payload message sending, in this case, the API could also be used directly (direct HTTP request from any shard) to bypass sharding.

## Message Payloads

### Bump Request

This message is sent when a user requests a bump.
| Key | Type | Description
| - | - | -
| type | MessageType | Always "REQUEST" in this type of message.
| guild | Snowflake (String) | The ID of the guild where the bump has been requested on.
| channel | Snowflake (Strnig) | The ID of the channel where the bump has been requested in.
| user | Snowflake (String) | The ID of the user that requested the bump.

### Bump Started Response

This message is sent once the bump request has been received to inform about the starting bump process.
| Key | Type | Description
| - | - | -
| type | MessageType | Always "START" in this type of response.
| response | Snowflake (String) | The ID of the message in which the bump was requested.

### Bump Finished Response

This message is sent once bumping has been finished (or once the bump has been added to the bump queue).
| Key | Type | Description
| - | - | -
| type | MessageType | Always "FINISHED" in this type of response.
| response | Snowflake (String) | The ID of the message in which the bump was requested.
| amount | Integer (Optional) | The amount of guilds where the guild has been bumped to.
| nextBump | Integer (Unix Milliseconds) | When the guild can be bumped again.
| message | String (Optional) | A custom success message. It is up to the bumping bot to display this message.

### Bump Error Response

This message is used to inform the bumping bot about an error that occured. It can only be sent once during a bump process and the bot should abort process after an error was sent.
| Key | Type | Description
| - | - | -
| type | MessageType | Always "ERROR" in this type of response
| response | Snowflake (String) | The ID of the message in which the bump was requested.
| code | ErrorCode | A code that can be used by the bumping bot to better understand the error message.
| nextBump | Integer (Unix Milliseconds, only on ErrorCode.COOLDOWN) | When the guild can be bumped again.
| message | String | A message explaining why the bump failed. IT is up to the bumping bot to display this message.

## Additional Objects

### MessageType Object

The MessageType object is used to identify the different types of message payloads.
| MessageType | Description
| - | -
| REQUEST | Used for bump requests.
| START | Used for bump started responses.
| FINISHED | Used for bump finished responses.
| ERROR | Used for bump error responses.

### ErrorCode Object

The ErrorCode object is used in the bump error response to allow the bumping bot to better understand the error. As these error codes can update, it is recommended to treat all unknown error codes equally to ErrorCode.OTHER and use a fallback error message.
| ErrorCode | Description
| - | -
| MISSING_SETUP | The guild has not finished setup with the repsonding bot yet.
| COOLDOWN | The guild is currently on cooldown with the responding bot.
| AUTOBUMP | This guild has autobump enabled and can not be bumped manually.
| NOT_FOUND | The receiving bot is not on the bumping guild.
| OTHER | If the error codes above do not fit the actual error.

## Authentication

Payload messages are sent by the actual bump bot. It is up to the receiving bot to determine which bots' requests will be interpreted.
We suggest to only interprete bump requests in a whitelisted channel.

# Suggestions

If you have any suggestions for this protocol, please create a pull request, and if you have any questions, please contact me on Discord. My tag is Looat#0001 and you can reach me on [this server](https://discord.gg/eBFu8HF).
