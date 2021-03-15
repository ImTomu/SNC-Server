import os

from server import database
from server.constants import TargetType
from server.exceptions import ClientError, ArgumentError, AreaError

from . import mod_only

__all__ = [
    'ooc_cmd_bg',
    'ooc_cmd_status',
    'ooc_cmd_area',
    'ooc_cmd_area_visible',
    'ooc_cmd_getarea',
    'ooc_cmd_getareas',
    'ooc_cmd_getafk',
    'ooc_cmd_invite',
    'ooc_cmd_uninvite',
    'ooc_cmd_area_kick',
    'ooc_cmd_pos_lock',
    'ooc_cmd_pos_lock_clear',
    'ooc_cmd_knock',
    'ooc_cmd_peek',
    'ooc_cmd_max_players',
    'ooc_cmd_desc',
    'ooc_cmd_edit_ambience',
]


def ooc_cmd_bg(client, arg):
    """
    Set the background of an area.
    Usage: /bg <background>
    """
    if len(arg) == 0:
        pos_lock = ''
        if len(client.area.pos_lock) > 0:
            pos = ' '.join(str(l) for l in client.area.pos_lock)
            pos_lock = f'\nAvailable positions: {pos}.'
        client.send_ooc(f'Current background is {client.area.background}.{pos_lock}')
        return
    if not client in client.area.area_manager.owners and not client.is_mod and client.area.bg_lock:
        raise AreaError("This area's background is locked")
    try:
        client.area.change_background(arg)
    except AreaError:
        raise
    client.area.broadcast_ooc(
        f'{client.showname} changed the background to {arg}.')
    database.log_room('bg', client, client.area, message=arg)


def ooc_cmd_status(client, arg):
    """
    Show or modify the current status of an area.
    Usage: /status <idle|rp|casing|looking-for-players|lfp|recess|gaming>
    """
    if not client.area.area_manager.arup_enabled:
        client.send_ooc('This hub does not use the /status system.')
        return
    if len(arg) == 0:
        client.send_ooc(f'Current status: {client.area.status}')
    else:
        if not client.area.can_change_status and not client.is_mod and not client in client.area.owners:
            client.send_ooc("This area's status cannot be changed by anyone who's not a CM or mod!")
            return
        try:
            client.area.change_status(arg)
            client.area.broadcast_ooc('{} changed status to {}.'.format(
                client.showname, client.area.status))
            database.log_room('status', client, client.area, message=arg)
        except AreaError:
            raise


def ooc_cmd_area(client, arg):
    """
    List areas, or go to another area.
    Usage: /area [id] or /area [name]
    """
    args = arg.split()
    if len(args) == 0:
        client.send_area_list(full=client.is_mod or client in client.area.owners)
        return

    try:
        for area in client.area.area_manager.areas:
            if (args[0].isdigit() and area.id == int(args[0])) or area.name.lower() == arg.lower() or area.abbreviation == arg:
                client.change_area(area)
                return
        raise AreaError('Targeted area not found!')
    except ValueError:
        raise ArgumentError('Area ID must be a name, abbreviation or a number.')
    except (AreaError, ClientError):
        raise


def ooc_cmd_area_visible(client, arg):
    """
    Display only linked and non-hidden areas. Useful to GMs.
    Usage: /area_visible
    """
    if arg != '':
        raise ArgumentError('This command takes no arguments!')
    client.send_area_list(full=False)


def ooc_cmd_getarea(client, arg):
    """
    Show information about the current area.
    Usage: /getarea
    """
    if client.blinded:
        raise ClientError('You are blinded!')
    client.send_area_info(client.area.id, False)



def ooc_cmd_getareas(client, arg):
    """
    Show information about all areas.
    Usage: /getareas
    """
    if client.blinded:
        raise ClientError('You are blinded!')
    client.send_area_info(-1, False)


def ooc_cmd_getafk(client, arg):
    """
    Show currently AFK-ing players in the current area or in all areas.
    Usage: /getafk [all]
    """
    if arg == 'all':
        arg = -1
    elif len(arg) == 0:
        arg = client.area.id
    else:
        raise ArgumentError('There is only one optional argument [all].')
    client.send_area_info(arg, False, afk_check=True)


@mod_only(area_owners=True)
def ooc_cmd_invite(client, arg):
    """
    Allow a particular user to join a locked or speak in spectator-only area.
    ID can be * to invite everyone in the current area.
    Usage: /invite <id>
    """
    if not arg:
        raise ClientError('You must specify a target. Use /invite <id>')
    elif client.area.is_locked == client.area.Locked.FREE:
        raise ClientError('Area isn\'t locked.')
    args = arg.split(' ')

    try:
        if args[0] == '*':
            targets = [c for c in client.area.clients if c != client and c != client.area.owners]
        else:
            targets = client.server.client_manager.get_targets(client, TargetType.ID,
                                                            int(args[0]), False)
    except ValueError:
        raise ArgumentError('Area ID must be a number or *.')

    try:
        for c in targets:
            client.area.invite_list.add(c.id)
            client.send_ooc(f'{c.showname} is invited to your area.')
            c.send_ooc(
                f'You were invited and given access to {client.area.name}.')
            database.log_room('invite', client, client.area, target=c)
    except:
        raise ClientError('You must specify a target. Use /invite <id>')


@mod_only(area_owners=True)
def ooc_cmd_uninvite(client, arg):
    """
    Revoke an invitation for a particular user.
    ID can be * to uninvite everyone in the area.
    Usage: /uninvite <id>
    """
    if client.area.is_locked == client.area.Locked.FREE:
        raise ClientError('Area isn\'t locked.')
    elif not arg:
        raise ClientError('You must specify a target. Use /uninvite <id>')
    args = arg.split(' ')
    try:
        if args[0] == '*':
            targets = [c for c in client.area.clients if c != client and c != client.area.owners]
        else:
            targets = client.server.client_manager.get_targets(client, TargetType.ID,
                                                            int(args[0]), False)
    except ValueError:
        raise ArgumentError('Area ID must be a number or *.')

    if targets:
        try:
            for c in targets:
                client.send_ooc(
                    "You have removed {} from the whitelist.".format(
                        c.showname))
                c.send_ooc(
                    "You were removed from the area whitelist.")
                database.log_room('uninvite', client, client.area, target=c)
                if client.area.is_locked != client.area.Locked.FREE:
                    client.area.invite_list.discard(c.id)
        except AreaError:
            raise
        except ClientError:
            raise
    else:
        client.send_ooc("No targets found.")


@mod_only(area_owners=True)
def ooc_cmd_area_kick(client, arg):
    """
    Remove a user from the current area and move them to another area.
    If id is a * char, it will kick everyone but you and CMs from current area to destination.
    If the destination is not specified, the destination defaults to area 0.
    target_pos is the optional position that everyone should end up in when kicked.
    Usage: /area_kick <id> [destination] [target_pos]
    """
    if not arg:
        raise ClientError(
            'You must specify a target. Use /area_kick <id> [destination #] [target_pos]')

    args = arg.split(' ')
    try:
        if args[0] == 'afk':
            targets = client.server.client_manager.get_targets(client, TargetType.AFK,
                                                            args[0], False)
        elif args[0] == '*':
            targets = [c for c in client.area.clients if c != client and c != client.area.owners]
        else:
            targets = client.server.client_manager.get_targets(client, TargetType.ID,
                                                            int(args[0]), False)
    except ValueError:
        raise ArgumentError('Area ID must be a number, afk or *.')

    if targets:
        try:
            for c in targets:
                # We're a puny CM, we can't do this.
                if not client.is_mod and not client in client.area.area_manager.owners and not c in client.area:
                    raise ArgumentError("You can't kick someone from another area as a CM!")
                if len(args) == 1:
                    area = client.area.area_manager.default_area()
                    output = area.id
                else:
                    try:
                        area = client.area.area_manager.get_area_by_id(
                            int(args[1]))
                        output = args[1]
                    except AreaError:
                        raise
                target_pos = ''
                if len(args) >= 3:
                    target_pos = args[2]
                client.send_ooc(
                    f'Attempting to kick {c.showname} to area {output}.')
                c.set_area(area, target_pos)
                c.send_ooc(
                    f"You were kicked from the area to area {output}.")
                database.log_room('area_kick', client, client.area, target=c, message=output)
                if client.area.is_locked != client.area.Locked.FREE:
                    client.area.invite_list.discard(c.id)
        except ValueError:
            raise ArgumentError('Area ID must be a number.')
        except AreaError:
            raise
        except ClientError:
            raise
    else:
        client.send_ooc("No targets found.")


def ooc_cmd_pos_lock(client, arg):
    """
    Lock current area's available positions into a list of pos separated by space.
    Use /pos_lock_clear to make the list empty.
    Usage:  /pos_lock <pos(s)>
    """
    if not arg:
        if len(client.area.pos_lock) > 0:
            pos = ' '.join(str(l) for l in client.area.pos_lock)
            client.send_ooc(f'Pos_lock is currently {pos}.')
        else:
            client.send_ooc('No pos lock set.')
        return

    if arg.strip().lower() == 'none':
        ooc_cmd_pos_lock_clear(client, arg)
        return

    if not client.is_mod and (client not in client.area.owners):
        raise ClientError('You must be authorized to do that.')

    client.area.pos_lock.clear()
    args = arg.split()
    args = sorted(set(args),key=args.index) #remove duplicates while preserving order
    for pos in args:
        pos = pos.lower()
        if pos == 'none':
            continue
        if len(pos) < 3:
            raise ClientError('Position names may not be shorter than 3 symbols!')
        client.area.pos_lock.append(pos)

    pos = ' '.join(str(l) for l in client.area.pos_lock)
    client.area.broadcast_ooc(f'Locked pos into {pos}.')
    client.area.send_command('SD', '*'.join(client.area.pos_lock)) #set that juicy pos dropdown


@mod_only(area_owners=True)
def ooc_cmd_pos_lock_clear(client, arg):
    """
    Clear the current area's position lock and make all positions available.
    Usage:  /pos_lock_clear
    """
    client.area.pos_lock.clear()
    client.area.broadcast_ooc('Position lock cleared.')


def ooc_cmd_knock(client, arg):
    """
    Knock on the target area ID to call on their attention to your area.
    Usage:  /knock <id>
    """
    args = arg.split()
    if len(args) == 0:
        raise ArgumentError('You need to input an accessible area name or ID to peek into it!')
    if client.blinded:
        raise ClientError('You are blinded!')
    try:
        area = None
        for _area in client.area.area_manager.areas:
            if (args[0].isdigit() and _area.id == int(args[0])) or _area.name.lower() == arg.lower() or _area.abbreviation == args[0]:
                area = _area
                break
        if area == None:
            raise ClientError('Target area not found.')
        if area == client.area:
            client.area.broadcast_ooc(f'[{client.id}] {client.showname} knocks for attention.')
            return
        allowed = client.is_mod or client in area.owners or client in client.area.owners
        if not allowed and client.area.is_locked == area.Locked.LOCKED and not client.id in client.area.invite_list:
            raise ClientError('Your current area is locked!')

        if len(client.area.links) > 0:
            if not str(area.id) in client.area.links and not allowed:
                raise ClientError('That area is inaccessible from your area!')

            if str(area.id) in client.area.links:
                # Get that link reference
                link = client.area.links[str(area.id)]

                # Link requires us to be inside a piece of evidence
                if len(link["evidence"]) > 0 and not (client.hidden_in in link["evidence"]) and not allowed:
                    raise ClientError('That area is inaccessible!')

        client.area.broadcast_ooc(f'[{client.id}] {client.showname} knocks on [{area.id}] {area.name}.')
        area.broadcast_ooc(f'!! Someone is knocking from [{client.area.id}] {client.area.name} !!')
    except ValueError:
        raise ArgumentError('Area ID must be a number or name.')
    except (AreaError, ClientError):
        raise


def ooc_cmd_peek(client, arg):
    """
    Peek into an area to see if there's people in it.
    Usage:  /peek <id>
    """
    args = arg.split()
    if len(args) == 0:
        raise ArgumentError('You need to input an accessible area name or ID to peek into it!')
    if client.blinded:
        raise ClientError('You are blinded!')
    try:
        area = None
        for _area in client.area.area_manager.areas:
            if (args[0].isdigit() and _area.id == int(args[0])) or _area.name.lower() == arg.lower() or _area.abbreviation == args[0]:
                area = _area
                break
        if area == None:
            raise ClientError('Target area not found.')
        if area == client.area:
            ooc_cmd_getarea(client, '')
            return

        sorted_clients = []
        for c in area.clients:
            if not c.hidden and not c in area.owners and not c.is_mod: #pure IC
                sorted_clients.append(c)

        # TODO: condense this monstrosity into a single func
        allowed = client.is_mod or client in area.owners or client in client.area.owners
        if not allowed and client.area.is_locked == area.Locked.LOCKED and not client.id in client.area.invite_list:
            raise ClientError('Your current area is locked!')

        if len(client.area.links) > 0:
            if not str(area.id) in client.area.links and not allowed:
                raise ClientError('That area is inaccessible from your area!')

            if str(area.id) in client.area.links:
                # Get that link reference
                link = client.area.links[str(area.id)]

                # Link requires us to be inside a piece of evidence
                if len(link["evidence"]) > 0 and not (client.hidden_in in link["evidence"]) and not allowed:
                    raise ClientError('That area is inaccessible!')

                # Our path is locked :(
                if link["locked"] and not allowed:
                    raise ClientError('That path is locked - cannot access area!')

                # Our path cannot be peeked through :(
                if not link["can_peek"] and not allowed:
                    raise ClientError('Cannot peek through that path!')

        if area.is_locked == area.Locked.LOCKED and not client.is_mod and not client.id in area.invite_list and not client.id in area.owners:
            raise ClientError('That area is locked!')

        _sort = [c.showname for c in sorted(sorted_clients, key=lambda x: x.showname)]

        # this would be nice to be a separate "make human readable list" func
        if len(_sort) == 2:
            sorted_clients = ' and '.join(_sort)
        elif len(_sort) > 2:
            sorted_clients = ', '.join(_sort[:-1])
            sorted_clients = "{} and {}".format(sorted_clients, _sort[-1])
        elif len(_sort) == 1:
            sorted_clients = _sort[0]

        if len(sorted_clients) <= 0:
            sorted_clients = 'nobody'

        client.area.broadcast_ooc(f'[{client.id}] {client.showname} peeks into [{area.id}] {area.name}...')
        client.send_ooc(f'There\'s {sorted_clients} in [{area.id}] {area.name}.')
    except ValueError:
        raise ArgumentError('Area ID must be a number or name.')
    except (AreaError, ClientError):
        raise


def ooc_cmd_max_players(client, arg):
    """
    Set a max amount of players for current area between -1 and 99.
    Usage: /max_players [num]
    """
    if arg == '':
        client.send_ooc(f'Max amount of players for the area is {client.area.max_players}.')
        return

    try:
        arg = int(arg)
        if arg < -1 or arg > 99:
            raise ClientError('The min-max values are -1 and 99!')
        client.area.max_players = arg
        client.send_ooc(f'New max amount of players for the area is now {client.area.max_players}.')
    except ValueError:
        raise ArgumentError('Area ID must be a name, abbreviation or a number.')
    except (AreaError, ClientError):
        raise


def ooc_cmd_desc(client, arg):
    """
    Set an area description that appears to the user any time they enter the area.
    Usage: /desc [desc]
    """
    if client.blinded:
        raise ClientError('You are blinded!')
    if len(arg) == 0:
        client.send_ooc(f'Description: {client.area.desc}')
        database.log_room('desc.request', client, client.area)
    else:
        client.area.desc = arg
        desc = arg[:128]
        if len(arg) > len(desc):
            desc += "... Use /desc to read the rest."
        client.area.broadcast_ooc(f'{client.showname} changed the area description to: {desc}.')
        database.log_room('desc.change', client, client.area, message=arg)


@mod_only(area_owners=True)
def ooc_cmd_edit_ambience(client, arg):
    """
    Toggle edit mode for setting ambience. Playing music will set it as the area's ambience.
    tog can be `on`, `off` or empty.
    Usage: /edit_ambience [tog]
    """
    if len(arg.split()) > 1:
        raise ArgumentError("This command can only take one argument ('on' or 'off') or no arguments at all!")
    if arg:
        if arg == 'on':
            client.edit_ambience = True
        elif arg == 'off':
            client.edit_ambience = False
        else:
            raise ArgumentError("Invalid argument: {}".format(arg))
    else:
        client.edit_ambience = not client.edit_ambience
    stat = 'no longer'
    if client.edit_ambience:
        stat = 'now'
    client.send_ooc(f'Playing a song will {stat} edit the area\'s ambience.')