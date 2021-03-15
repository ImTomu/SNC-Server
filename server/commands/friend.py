from server import database
from server.constants import TargetType
from server.exceptions import ClientError, ArgumentError

from . import mod_only

__all__ = [
    'ooc_cmd_friend',
    'ooc_cmd_unfriend',
    'ooc_cmd_friendlist'
]

def ooc_cmd_friend(client, arg):
    if len(arg) == 0:
        if len(client.friendrequests) != 0:
            msg = 'Friend Requests:'
            for request in client.friendrequests:
                msg += f'\n[{request.id}]{request.name}.'
            msg += '\nUse /friend <id> to accept a request.'
            client.send_ooc(msg)
            return
        else:
            raise ArgumentError('No pending friend requests. Use /friend <id> to send a friend request to someone else.')
    try:
        arg = int(arg)
    except:
        raise ArgumentError('You must specify a target. Use /friend <id>.')
    for c in client.server.client_manager.clients:
        if c.id == arg:
            if c is client:
                raise ArgumentError('Cannot befriend yourself.')
            if c in client.friendrequests:
                client.friendlist.addfriend(c.hdid, c.name)
                client.send_ooc(f'added {c.name} to your friend list!')
                c.send_ooc(f'{client.name} accepted your friend request!')
                client.friendrequests.remove(c)
                return
            else:
                for hdid, name in client.friendlist.friends.items():
                    if c.hdid == hdid:
                        raise ArgumentError('You are already friends with that person!')
                c.friendrequests.add(client)
                c.send_ooc(f'You received a friend request from [{client.id}]{client.name}! Use /friend <id> to accept their request.')
                client.send_ooc(f'Friend request sent to {c.char_name}.')
                return
    client.send_ooc('No targets found.')

def ooc_cmd_unfriend(client, arg):
    if len(arg) == 0:
        raise ArgumentError('You need to specify an ID to unfriend.')
    try:
        arg = int(arg)
    except:
        raise ArgumentError('You must specify a target. Use /unfriend <id>.')
    for c in client.server.client_manager.clients:
        if c.id == arg:
            if c.hdid not in client.friendlist.friends:
                raise ArgumentError('That person is not on your friend list.')
            client.friendlist.removefriend(c.hdid)
            client.send_ooc('Friend removed.')
            return
    raise ArgumentError('That person is not on your friend list.')

def ooc_cmd_friendlist(client, arg):
    if len(arg) > 0:
        raise ArgumentError('This takes no arguments.')
    client.friendlist.loadfriends()
    if len(client.friendlist.friends) == 0:
        raise ArgumentError('You have no friends.')
    msg = 'Friend List:'
    for hdid, name in client.friendlist.friends.items():
        online = False
        msg += f'\n{name}: '
        fhdid = hdid
        for c in client.server.client_manager.clients:
            if c.hdid == fhdid:
                msg += f'Online as [{c.id}]{c.char_name}.'
                online = True
                break
        if not online:
            msg += 'Offline.'
    client.send_ooc(msg)