from server import database
from server.constants import TargetType
from server.exceptions import *
from server.party import Party, Vote
from . import mod_only

__all__ = [
    'ooc_cmd_party',
    'ooc_cmd_parties',
    'ooc_cmd_lockparty',
    'ooc_cmd_unlockparty',
    'ooc_cmd_destroyparty',
    'ooc_cmd_joinparty',
    'ooc_cmd_leaveparty',
    'ooc_cmd_partykick',
    'ooc_cmd_createparty',
    'ooc_cmd_partyinvite',
    'ooc_cmd_partypm',
    'ooc_cmd_partynote',
    'ooc_cmd_clearpartynote',
    'ooc_cmd_startmgvote',
    'ooc_cmd_revealmgvote',
    'ooc_cmd_mgvote',
    'ooc_cmd_mgroles',
    'ooc_cmd_mgvp',
    'ooc_cmd_addrole',
    'ooc_cmd_clearroles',
    'ooc_cmd_rolesvisible'
]

def ooc_cmd_party(client, arg):
    if len(arg) > 0:
        raise ArgumentError('This command takes no arguments.')
    if not client.in_party:
        ooc_cmd_parties(client, arg)
    else:
        party = client.party
        users = party.users
        msg = f'Party Members: {len(users)}\n=== {party.name} ==='
        if party.leader not in users:
            for member in users:
                if party.leader not in users:
                    party.leader = member
                    member.send_ooc('Party Leader left, you are now the new Party Leader.')
            else:
                member.send_ooc(f'Party Leader left, {party.leader.name} is the new Party Leader.')
        for member in users:
            msg += f'\n[{member.area.name}][{member.id}] {member.char_name}: {member.name}'
            if party.leader == member:
                msg += ' (Party Leader)'
            if party.rolesvisible:
                if member.partyrole != '':
                    msg += f' ({member.partyrole})'
            elif party.leader == client:
                if member.partyrole != '':
                    msg += f' ({member.partyrole})'
            elif member == client and member != party.leader:
                if member.partyrole != '':
                    msg += f' ({member.partyrole})'
        client.send_ooc(msg)


def ooc_cmd_parties(client, arg):
    if len(arg) > 0:
        raise ArgumentError('This command takes no arguments.')
    if len(client.server.parties) != 0:
        msg = 'Current parties:'
        parties = client.server.parties
        for party in parties:
            if len(party.users) == 0:
                client.server.parties.remove(party)
                if len(client.server.parties) == 0:
                    raise ClientError('No parties currently on the server.')
            if party.leader not in party.users:
                for member in party.users:
                    if party.leader not in party.users:
                        party.leader = member
                        member.send_ooc('Party Leader left, you are now the new Party Leader.')
                    else:
                        member.send_ooc(f'Party Leader left, {party.leader.name} is the new Party Leader.')
            if party.lock:
                lock = 'Private'
            else:
                lock = 'Public'
            msg += f'\n===================\n[{party.id}] {party.name} [{len(party.users)} Members][{lock}]'
            msg += f'\nParty Leader: [{party.leader.id}] {party.leader.name}.'
        msg += '\n==================='
        client.send_ooc(msg)
    else:
        raise ClientError('No parties currently on the server.')


def ooc_cmd_lockparty(client, arg):
    if not client.in_party:
        raise ClientError('You aren\'t in a party.')
    if client.party.leader != client:
        raise ClientError('You are not the party leader.')
    if client.party.lock:
        raise ArgumentError('This party is already private.')
    client.party.lock = True
    client.send_ooc(f'{client.party.name} is now private.')


def ooc_cmd_unlockparty(client, arg):
    if not client.in_party:
        raise ClientError('You aren\'t in a party.')
    if client.party.leader != client:
        raise ClientError('You are not the party leader.')
    if not client.party.lock:
        raise ArgumentError('This party is already public.')
    client.party.lock = False
    client.send_ooc(f'{client.party.name} is now public.')


def ooc_cmd_destroyparty(client, arg):
    if not client.in_party and not client.is_mod:
        raise ClientError('You aren\'t in a party.')
    if not client.is_mod and client.party.leader != client:
        raise ClientError('You are not the party leader.')
    if len(arg) == 0:
        partyusers = set()
        for member in client.party.users:
            partyusers.add(member)
        for member in partyusers:
            client.party.users.remove(member)
            member.party = None
            member.in_party = False
            member.partyrole = ''
            member.votepower = 0
            member.send_ooc(f'Party Leader destroyed party!')
        client.server.parties.remove(client.party)
    elif client.is_mod:
        try:
            id = int(arg)
        except:
            raise ArgumentError(f'{id} does not look like a valid ID.')
        for party in client.server.parties:
            parties = []
            parties.add(party)
        for party in parties:
            if id == party.id:
                partyusers = set()
                for member in client.party.users:
                    partyusers.add(member)
                for member in partyusers:
                    client.party.users.remove(member)
                    member.party = None
                    member.in_party = False
                    member.partyrole = ''
                    member.votepower = 0
                    member.send_ooc('Party was destroyed!')
                client.server.parties.remove(party)
                return
        raise ArgumentError(f'{arg} does not look like a valid party ID.')
    else:
        raise ArgumentError('Too many arguments.')


def ooc_cmd_joinparty(client, arg):
    if len(arg) != 1:
        raise ArgumentError('Not enough arguments, use /joinparty <id>.')
    if client.in_party:
        raise ClientError('You are already in a party!')
    else:
        try:
            id = int(arg)
        except:
            raise ArgumentError(f'{id} does not look like a valid ID.')
        for party in client.server.parties:
            if id == party.id:
                if party.lock:
                    if not client.is_mod and client.id not in party.invite_list:
                        raise ClientError('Group is private!')
                    else:
                        for user in party.users:
                            user.send_ooc(f'{client.name} joined {party.name}.')
                        party.add_user(client)
                        client.party = party
                        client.in_party = True
                        client.send_ooc(f'Joined {party.name}.')
                        return
                else:
                    for user in party.users:
                        user.send_ooc(f'{client.name} joined {party.name}.')
                    party.add_user(client)
                    client.party = party
                    client.in_party = True
                    client.send_ooc(f'Joined {party.name}.')
                    return
        raise ArgumentError(f'{arg} does not look like a valid ID.')


def ooc_cmd_leaveparty(client, arg):
    if not client.in_party:
        raise ClientError('You aren\'t in a party.')
    party = client.party
    party.users.remove(client)
    client.party = None
    client.in_party = False
    client.partyrole = ''
    client.votepower = 0
    if len(party.users) != 0:
        client.area.send_ooc(f'Left {party.name}.')
        if party.leader == client:
            for member in party.users:
                if party.leader not in party.users:
                    party.leader = member
                    member.send_ooc('Party Leader left, you are now the new Party Leader.')
                else:
                    member.send_ooc(f'Party Leader left, {party.leader.name} is the new Party Leader.')
    else:
        client.server.parties.remove(party)
        client.send_ooc(f'Left {party.name}. Party was destroyed.')


def ooc_cmd_partykick(client, arg):
    if not client.in_party:
        raise ClientError('You aren\'t in a party.')
    if not client.is_mod and client.party.leader != client:
        raise ClientError('You are not the party leader.')
    if len(arg) != 1:
        raise ArgumentError('Not enough arguments, use /joinparty <id>.')
    else:
        try:
            id = int(arg)
        except:
            raise ArgumentError(f'{id} does not look like a valid ID.')
    party = client.party
    users = set()
    for member in party.users:
        users.add(member)
    for member in users:
        if member.id == id:
            client.party.users.remove(member)
            member.party = None
            member.in_party = False
            member.partyrole = ''
            member.votepower = 0
            member.send_ooc('You were kicked from the party!')
            client.send_ooc(f'Kicked {member.name} from the party.')
            return
    raise ArgumentError(f'{id} does not look like a valid ID.')


def ooc_cmd_createparty(client, arg):
    if client.in_party:
        raise ClientError('You are already in a party!')
    if len(arg) == 0:
        raise ArgumentError('Not enough arguments, use /createparty <name>.')
    if len(arg) > 32:
        raise ArgumentError('That name is too long!')
    id = len(client.server.parties)
    client.party = Party(client.server, arg, client, id)
    client.server.parties.append(client.party)
    client.in_party = True
    client.send_ooc(f'Created party {client.party.name}.')


def ooc_cmd_partyinvite(client, arg):
    """
    Allow a particular user to join a locked or spectator-only area.
    Usage: /invite <id>
    """
    if not arg:
        raise ClientError('You must specify a target. Use /partyinvite <id>')
    elif not client.in_party:
        raise ClientError('You aren\'t in a party.')
    elif client.party.leader != client:
        raise ClientError('You are not the party leader, ask them to invite.')
    try:
        c = client.server.client_manager.get_targets(client, TargetType.ID, int(arg), False)[0]
        client.party.invite_list[c.id] = None
        client.send_ooc('{} is invited to your group.'.format(c.name))
        c.send_ooc(f'You were invited and given access to {client.party.name}.')
    except:
        raise ClientError('You must specify a target. Use /partyinvite <id>')

def ooc_cmd_partypm(client, arg):
    if not client.in_party:
        raise ClientError('You aren\'t in a party.')
    args = arg.split()
    if len(args) < 2:
        raise ArgumentError('Not enough arguments. use /partypm <target> <message>. Target should be an ID. Use /party for getting info like "[ID] char-name".')
    msg = ' '.join(args[1:])
    tryint = ignore_exception(ValueError)(int)
    id = tryint(arg[0])
    if id is None:
        raise ArgumentError(f'{id} does not look like a valid ID.')
    for c in client.party.users:
        if id == c.id:
            if c.is_mod:
                c.send_ooc('PM from {} (ID: {}, IPID: {}) in {} ({}): {}'.format(client.name, client.id, client.ipid, client.hub.name, client.name, msg))
            else:
                c.send_ooc('PM from {} (ID: {}) in {} ({}): {}'.format(client.name, client.id, client.hub.name, client.name, msg))
            client.send_ooc('PM sent to [{}] {}. Message: {}'.format(c.id, c.name, msg))
            return
    raise ClientError('You must specify a target. Use /partypm <id> <message')

def ooc_cmd_partynote(client, arg):
    """
    Adds to the client's notes.
    """
    notepad = 'Party Notepad:'
    if not client.in_party:
        raise ClientError('You aren\'t in a party.')
    if len(arg) > 256:
        raise ArgumentError('That note is too large to add to your notes!')
    elif len(arg) == 0:
        if client.party.notepad == '':
            notepad += '\nNothing is on the notepad.'
            client.send_ooc(notepad)
        else:
            notepad += client.party.notepad
            client.send_ooc(notepad)
    else:
        if len(client.party.notepad) > 4000:
            raise ArgumentError('Your notes exceed the maximum of 4000 characters!')
        else:
            client.party.notepad += f'\n{arg}'
            for user in client.party.users:
                user.send_ooc(f'{client.name} added a note to the party notepad.')

def ooc_cmd_clearpartynote(client, arg):
    """
    Clears the client's notes.
    """
    if not client.in_party:
        raise ClientError('You aren\'t in a party.')
    if client.party.leader != client:
        raise ClientError('You aren\'t the Party Leader.')
    if len(arg) > 0:
        raise ArgumentError('This command takes no arguments.')
    else:
        client.party.notepad = ''
        for user in client.party.users:
            user.send_ooc(f'Party notepad was cleared.')

def ooc_cmd_startmgvote(client, arg):
    if not client.in_party:
        raise ClientError('You aren\'t in a party.')
    if client.party.leader != client and not client.is_mod:
        raise ClientError('You are not the party leader.')
    if len(arg) == 0:
        raise ArgumentError('Not enough arguments, use /startmgvote <arguments>.')
    args = arg.split()
    party = client.party
    party.votes = set()
    msg = 'Vote started with arguments: '
    for a in args:
        vote = Vote(a)
        party.votes.add(vote)
        msg += f'"{a}" '
    for user in party.users:
        user.send_ooc(msg)
        if user.partyrole == 'Sacrifice':
            user.votepower = 1
        else:
            user.votepower = 0

def ooc_cmd_revealmgvote(client, arg):
    if not client.in_party:
        raise ClientError('You aren\'t in a party.')
    if len(client.party.votes) == 0:
        raise ClientError('No ongoing vote.')
    msg = 'Party Vote:'
    for vote in client.party.votes:
        msg += f'\n{vote.name}: {vote.number} vote(s).'
    client.party.votes = set()
    client.area.send_ooc(msg)
    for user in client.party.users:
        user.send_ooc(msg)
        if user.partyrole == 'Sacrifice':
            user.votepower = 1
        else:
            user.votepower = 0


def ooc_cmd_mgvote(client, arg):
    if not client.in_party:
        raise ClientError('You aren\'t in a party.')
    if len(client.party.votes) == 0:
        raise ClientError('No ongoing vote.')
    if len(arg) == 0:
        if client.party.leader == client:
            msg = 'Party Vote:'
            for vote in client.party.votes:
                msg += f'\n{vote.name}: {vote.number} vote(s).'
            client.send_ooc(msg)
            return
    if client.votepower < 0:
        raise ClientError('You can\'t vote again.')
    for vote in client.party.votes:
        if vote.name == arg:
            vote.number += 1
            client.votepower -= 1
            vote.voters.add(client)
            client.send_ooc(f'Voted for {arg}.')
            client.party.leader.send_ooc(f'{client.char_name} voted for {arg}.')
            return
    raise ArgumentError('Invalid argument.')


def ooc_cmd_mgroles(client, arg):
    if not client.in_party:
        raise ClientError('You aren\'t in a party.')
    if client.party.leader != client:
        raise ClientError('You are not the party leader.')
    for user in client.party.users:
        user.partyrole = ''
        user.votepower = 0
    if len(arg) == 0:
        if len(client.party.users) < 5:
            raise ArgumentError('Not enough players to hand out the roles!')
        else:
            client.send_ooc(client.party.mg_roles(arg))
            for user in client.party.users:
                if user.partyrole != '':
                    user.send_ooc(f'Your role is now {user.partyrole}.')
    else:
        args = arg.split()
        check = 5 + len(args)
        if len(client.party.users) < check:
            raise ArgumentError('Not enough players to hand out the roles!')
        client.send_ooc(client.party.mg_roles(args))
        for user in client.party.users:
            if user.partyrole != '':
               user.send_ooc(f'Your role is now {user.partyrole}.')

def ooc_cmd_mgvp(client, arg):
    if not client.in_party:
        raise ClientError('You aren\'t in a party.')
    if len(arg) == 0:
        raise ArgumentError('Not enough arguments.')
    args = arg.split()
    id = int(args[0])
    if len(args) == 1:
        for user in client.party.users:
            if user.partyrole != '':
                client.send_ooc(f'{user.name}\'s vote power is {user.votepower}.')
    elif len(args) == 2:
        if args[1] == '+':
            for user in client.party.users:
                if user.id == id:
                    user.votepower += 1
                    client.send_ooc('{user.name}\s vote power has been increased by one.')
                    return
        elif args[1] == '-':
            for user in client.party.users:
                if user.id == id:
                    user.votepower -= 1
                    client.send_ooc('{user.name}\s vote power has been decreased by one.')
                    return
    else:
        raise ArgumentError('Too many arguments. Use /mgvp <id> <+ or -> or /mgvp <id>.')


def ooc_cmd_addrole(client, arg):
    if not client.in_party:
        raise ClientError('You aren\'t in a party.')
    if not client.is_mod and client.party.leader != client:
        raise ClientError('You are not the party leader.')
    if len(arg) == 0:
        raise ArgumentError('Too many arguments! Use /addrole [id] [role].')
    else:
        tryint = ignore_exception(ValueError)(int)
        arg = arg.split()
        id = tryint(arg[0])
        if id is None:
            raise ArgumentError(f'{id} does not look like a valid ID.')
    if len(arg) < 2:
        raise ArgumentError('Not enough arguments! Use /addrole [id] [role].')
    party = client.party
    for member in party.users:
        if member.id == id:
            member.partyrole = arg[1]
            member.votepower = 0
            member.send_ooc(f'Your role is now {member.partyrole}')
            client.send_ooc(f'Assigned {arg[1]} to {member.name}.')
            return
    raise ArgumentError(f'{id} does not look like a valid ID.')

def ooc_cmd_rolesvisible(client, arg):
    if not client.in_party:
        raise ClientError('You aren\'t in a party.')
    if client.party.leader != client:
        raise ClientError('You are not the party leader.')
    if len(arg) > 0:
        raise ArgumentError('Too many arguments.')
    if client.party.rolesvisible:
        client.party.rolesvisible = False
        for member in client.party.users:
            member.send_ooc('Party roles are no longer visible.')
    else:
        client.party.rolesvisible = True
        for member in client.party.users:
            member.send_ooc('Party roles are now visible.')

def ooc_cmd_clearroles(client, arg):
    if not client.in_party:
        raise ClientError('You aren\'t in a party.')
    if client.party.leader != client:
        raise ClientError('You are not the party leader.')
    for user in client.party.users:
        user.partyrole = ''
        user.votepower = 0