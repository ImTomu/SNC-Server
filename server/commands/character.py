import random

from server import database
from server.constants import TargetType
from server.exceptions import ClientError, ServerError, ArgumentError, AreaError

from . import mod_only

__all__ = [
    'ooc_cmd_switch',
    'ooc_cmd_pos',
    'ooc_cmd_forcepos',
    'ooc_cmd_charselect',
    'ooc_cmd_randomchar',
    'ooc_cmd_charcurse',
    'ooc_cmd_uncharcurse',
    'ooc_cmd_charids',
    'ooc_cmd_reload',
    'ooc_cmd_blind',
    'ooc_cmd_unblind',
    'ooc_cmd_player_move_delay',
    'ooc_cmd_player_hide',
    'ooc_cmd_player_unhide',
    'ooc_cmd_hide',
    'ooc_cmd_unhide',
    'ooc_cmd_sneak',
    'ooc_cmd_unsneak',
    'ooc_cmd_listen_pos',
    'ooc_cmd_unlisten_pos',
    'ooc_cmd_save_character_data',
    'ooc_cmd_load_character_data',
]


def ooc_cmd_switch(client, arg):
    """
    Switch to another character. If moderator and the specified character is
    currently being used, the current user of that character will be
    automatically reassigned a character.
    Usage: /switch <name>
    """
    if len(arg) == 0:
        raise ArgumentError('You must specify a character name.')
    try:
        cid = client.server.get_char_id_by_name(arg)
    except ServerError:
        raise
    try:
        client.change_character(cid, client.is_mod)
    except ClientError:
        raise
    client.send_ooc('Character changed.')


def ooc_cmd_pos(client, arg):
    """
    Set the place your character resides in the room.
    Usage: /pos <name>
    """
    if len(arg) == 0:
        client.change_position()
        client.send_ooc('Position reset.')
    else:
        try:
            client.change_position(arg)
        except ClientError:
            raise
        client.area.broadcast_evidence_list()
        client.send_ooc('Position changed.')


@mod_only(area_owners=True)
def ooc_cmd_forcepos(client, arg):
    """
    Set the place another character resides in the room.
    Usage: /forcepos <pos> <target>
    """
    args = arg.split()

    if len(args) < 1:
        raise ArgumentError(
            'Not enough arguments. Use /forcepos <pos> <target>. Target should be ID, OOC-name or char-name. Use /getarea for getting info like "[ID] char-name".'
        )

    targets = []

    pos = args[0]
    if len(args) > 1:
        targets = client.server.client_manager.get_targets(
            client, TargetType.CHAR_NAME, " ".join(args[1:]), True)
        if len(targets) == 0 and args[1].isdigit():
            targets = client.server.client_manager.get_targets(
                client, TargetType.ID, int(args[1]), True)
        if len(targets) == 0:
            targets = client.server.client_manager.get_targets(
                client, TargetType.OOC_NAME, " ".join(args[1:]), True)
        if len(targets) == 0:
            raise ArgumentError('No targets found.')
    else:
        for c in client.area.clients:
            targets.append(c)

    for t in targets:
        try:
            t.change_position(pos)
            t.area.broadcast_evidence_list()
            t.send_ooc(f'Forced into /pos {pos}.')
            database.log_room('forcepos', client, client.area, target=t, message=pos)
        except ClientError:
            raise

    client.area.broadcast_ooc(
        '{} forced {} client(s) into /pos {}.'.format(client.char_name,
                                                      len(targets), pos))


def ooc_cmd_charselect(client, arg):
    """
    Enter the character select screen, or force another user to select
    another character.
    Usage: /charselect [id]
    """
    if not arg:
        client.char_select()
    else:
        force_charselect(client, arg)


@mod_only()
def force_charselect(client, arg):
    try:
        client.server.client_manager.get_targets(client, TargetType.ID,
            int(arg), False)[0].char_select()
    except:
        raise ArgumentError('Wrong arguments. Use /charselect <target\'s id>')


def ooc_cmd_randomchar(client, arg):
    """
    Select a random character.
    Usage: /randomchar
    """
    if len(arg) != 0:
        raise ArgumentError('This command has no arguments.')
    if len(client.charcurse) > 0:
        free_id = random.choice(client.charcurse)
    else:
        try:
            free_id = client.area.get_rand_avail_char_id()
        except AreaError:
            raise
    try:
        client.change_character(free_id)
    except ClientError:
        raise
    client.send_ooc('Randomly switched to {}'.format(
        client.char_name))


@mod_only()
def ooc_cmd_charcurse(client, arg):
    """
    Lock a user into being able to choose only from a list of characters.
    Usage: /charcurse <id> [charids...]
    """
    if len(arg) == 0:
        raise ArgumentError(
            'You must specify a target (an ID) and at least one character ID. Consult /charids for the character IDs.'
        )
    elif len(arg) == 1:
        raise ArgumentError(
            'You must specific at least one character ID. Consult /charids for the character IDs.'
        )
    args = arg.split()
    try:
        targets = client.server.client_manager.get_targets(
            client, TargetType.ID, int(args[0]), False)
    except:
        raise ArgumentError(
            'You must specify a valid target! Make sure it is a valid ID.')
    if targets:
        for c in targets:
            log_msg = ''
            part_msg = ' [' + str(c.id) + '] to'
            for raw_cid in args[1:]:
                try:
                    cid = int(raw_cid)
                    c.charcurse.append(cid)
                    part_msg += ' ' + str(client.server.char_list[cid]) + ','
                    log_msg += ' ' + str(client.server.char_list[cid]) + ','
                except:
                    ArgumentError('' + str(raw_cid) +
                                  ' does not look like a valid character ID.')
            part_msg = part_msg[:-1]
            part_msg += '.'
            log_msg = log_msg[:-1]
            c.char_select()
            database.log_room('charcurse', client, client.area, target=c, message=log_msg)
            client.send_ooc('Charcursed' + part_msg)
    else:
        client.send_ooc('No targets found.')


@mod_only()
def ooc_cmd_uncharcurse(client, arg):
    """
    Remove the character choice restrictions from a user.
    Usage: /uncharcurse <id>
    """
    if len(arg) == 0:
        raise ArgumentError('You must specify a target (an ID).')
    args = arg.split()
    try:
        targets = client.server.client_manager.get_targets(
            client, TargetType.ID, int(args[0]), False)
    except:
        raise ArgumentError(
            'You must specify a valid target! Make sure it is a valid ID.')
    if targets:
        for c in targets:
            if len(c.charcurse) > 0:
                c.charcurse = []
                database.log_room('uncharcurse', client, client.area, target=c)
                client.send_ooc(f'Uncharcursed [{c.id}].')
                c.char_select()
            else:
                client.send_ooc(f'[{c.id}] is not charcursed.')
    else:
        client.send_ooc('No targets found.')


@mod_only()
def ooc_cmd_charids(client, arg):
    """
    Show character IDs corresponding to each character name.
    Usage: /charids
    """
    if len(arg) != 0:
        raise ArgumentError("This command doesn't take any arguments")
    msg = 'Here is a list of all available characters on the server:'
    for c in range(0, len(client.server.char_list)):
        msg += '\n[' + str(c) + '] ' + client.server.char_list[c]
    client.send_ooc(msg)


def ooc_cmd_reload(client, arg):
    """
    Reload a character to its default position and state.
    Usage: /reload
    """
    if len(arg) != 0:
        raise ArgumentError("This command doesn't take any arguments")
    try:
        client.reload_character()
    except ClientError:
        raise
    client.send_ooc('Character reloaded.')


@mod_only()
def ooc_cmd_blind(client, arg):
    """
    Blind the targeted player(s) from being able to see or talk IC.
    Usage: /blind <id> [id(s)]
    """
    if len(arg) == 0:
        raise ArgumentError('You must specify a target.')
    try:
        targets = []
        ids = [int(s) for s in arg.split(' ')]
        for targ_id in ids:
            c = client.server.client_manager.get_targets(client, TargetType.ID, targ_id, False)
            if c:
                targets = targets + c
    except:
        raise ArgumentError('You must specify a target. Use /blind <id>.')

    if targets:
        for c in targets:
            if c.blinded:
                client.send_ooc(f'Client [{c.id}] {c.name} already blinded!')
                continue
            c.blind(True)
            client.send_ooc(f'You have blinded [{c.id}] {c.name} from using /getarea and seeing non-broadcasted IC messages.')
    else:
        raise ArgumentError('No targets found.')


@mod_only()
def ooc_cmd_unblind(client, arg):
    """
    Undo effects of the /blind command.
    Usage: /unblind <id> [id(s)]
    """
    if len(arg) == 0:
        raise ArgumentError('You must specify a target.')
    try:
        targets = []
        ids = [int(s) for s in arg.split(' ')]
        for targ_id in ids:
            c = client.server.client_manager.get_targets(client, TargetType.ID, targ_id, False)
            if c:
                targets = targets + c
    except:
        raise ArgumentError('You must specify a target. Use /unblind <id>.')

    if targets:
        for c in targets:
            if not c.blinded:
                client.send_ooc(f'Client [{c.id}] {c.name} already unblinded!')
                continue
            c.blind(False)
            client.send_ooc(f'You have unblinded [{c.id}] {c.name}.')
    else:
        raise ArgumentError('No targets found.')


@mod_only()
def ooc_cmd_player_move_delay(client, arg):
    """
    Set the player's move delay to a value in seconds. Can be negative.
    Delay must be from -1800 to 1800 in seconds or empty to check.
    Usage: /player_move_delay <id> [delay] OR /player_move_delay <delay>
    """
    args = arg.split()
    try:
        c = client
        if len(args) > 0:
            move_delay = int(args[0])
            if len(args) > 1:
                c = client.server.client_manager.get_targets(client, TargetType.ID,
                                                            int(arg), False)[0]
                move_delay = int(args[1])
            move_delay = min(1800, max(-1800, move_delay)) # Move delay is limited between -1800 and 1800
            c.move_delay = move_delay
            client.send_ooc(f'Set move delay for [{c.id}] {c.char_name} to {move_delay}.')
        else:
            client.send_ooc(f'Current move delay for [{c.id}] {c.char_name} is {c.move_delay}.')
    except ValueError:
        raise ArgumentError('Delay must be an integer between -1800 and 1800.')
    except IndexError:
        raise ArgumentError('Target client not found. Use /player_move_delay <id> [delay], or /player_move_delay <delay>.')
    except (AreaError, ClientError):
        raise


@mod_only()
def ooc_cmd_player_hide(client, arg):
    """
    Hide player(s) from /getarea and playercounts.
    If <id> is *, it will hide everyone in the area excluding yourself and CMs.
    Usage: /player_hide <id> [id(s)]
    """
    if len(arg) == 0:
        raise ArgumentError('You must specify a target.')
    args = arg.split()
    if args[0] == '*':
        targets = [c for c in client.area.clients if c != client and c != client.area.owners]
    else:
        try:
            targets = []
            ids = [int(s) for s in args]
            for targ_id in ids:
                c = client.server.client_manager.get_targets(client, TargetType.ID, targ_id, False)
                if c:
                    targets = targets + c
        except:
            raise ArgumentError('You must specify a target. Use /player_unhide <id> [id(s)].')
    if targets:
        for c in targets:
            if c.hidden:
                raise ClientError(
                    f'Client [{c.id}] {c.char_name} already hidden!')
            c.hide(True)
            client.send_ooc(
                f'You have hidden [{c.id}] {c.char_name} from /getarea and playercounts.')
    else:
        client.send_ooc('No targets found.')


@mod_only()
def ooc_cmd_player_unhide(client, arg):
    """
    Unhide player(s) from /getarea and playercounts.
    If <id> is *, it will hide everyone in the area excluding yourself and CMs.
    Usage: /player_unhide <id> [id(s)]
    """
    if len(arg) == 0:
        raise ArgumentError('You must specify a target.')
    args = arg.split()
    if args[0] == '*':
        targets = [c for c in client.area.clients if c != client and c != client.area.owners]
    else:
        try:
            targets = []
            ids = [int(s) for s in args]
            for targ_id in ids:
                c = client.server.client_manager.get_targets(client, TargetType.ID, targ_id, False)
                if c:
                    targets = targets + c
        except:
            raise ArgumentError('You must specify a target. Use /player_unhide <id> [id(s)].')
    if targets:
        for c in targets:
            if not c.hidden:
                raise ClientError(
                    f'Client [{c.id}] {c.char_name} already revealed!')
            c.hide(False)
            client.send_ooc(
                f'You have revealed [{c.id}] {c.char_name} for /getarea and playercounts.')
    else:
        client.send_ooc('No targets found.')

def ooc_cmd_hide(client, arg):
    """
    Try to hide in the targeted evidence name or ID.
    Usage: /hide <evi_name/evi_id>
    """
    if arg == '':
        raise ArgumentError('Use /hide <evi_name/evi_id> to hide in evidence, or /unhide to stop hiding.')
    try:
        client.hide(True, arg)
    except ValueError:
        raise
    except (AreaError, ClientError):
        raise


def ooc_cmd_unhide(client, arg):
    """
    Stop hiding.
    Usage: /unhide
    """
    if client.hidden_in != None and client.hidden_in in client.area.evi_list.evidences:
        client.area.broadcast_ooc(f'{client.char_name} emerges from the {client.area.evi_list.evidences[client.hidden_in]}!')
    client.hide(False)

def ooc_cmd_sneak(client, arg):
    """
    Begin sneaking a.k.a. hide your area moving messages from the OOC.
    Usage: /sneak
    """
    if arg != '':
        raise ArgumentError('This command takes no arguments!')
    if client.sneaking:
        raise ClientError('You are already sneaking! Use /unsneak to stop sneaking.')
    client.sneak(True)


def ooc_cmd_unsneak(client, arg):
    """
    Stop sneaking a.k.a. show your area moving messages in the OOC.
    Usage: /sneak
    """
    if arg != '':
        raise ArgumentError('This command takes no arguments!')
    if not client.sneaking:
        raise ClientError('You are not sneaking! Use /sneak to start sneaking.')
    client.sneak(False)


def ooc_cmd_listen_pos(client, arg):
    """
    Start only listening to your currently occupied pos.
    All messages outside of that pos will be reflected in the OOC.
    Optional argument is a list of positions you want to listen to.
    Usage: /listen_pos [pos1] [pos2] [posX]
    """
    args = arg.split()
    value = 'self'
    if len(args) > 0:
        value = args

    client.listen_pos = value
    if value == 'self':
        value = f'listening to your own pos {client.pos}'
    else:
        value = ', '.join(value)
        value = f'listening to pos {value}'
    client.send_ooc(f'You are {value}. Use /unlisten_pos to stop listening.')


def ooc_cmd_unlisten_pos(client, arg):
    """
    Undo the effects of /listen_pos command so you stop listening to the position(s).
    Usage: /unlisten_pos
    """
    if client.listen_pos == None:
        raise ClientError('You are not listening to any pos at the moment!')
    client.listen_pos = None
    client.send_ooc(f'You re no longer listening to any pos (All IC messages will appear as normal).')


@mod_only()
def ooc_cmd_save_character_data(client, arg):
    """
    Save the move_delay, keys, etc. for characters into a file in the storage/character_data/ folder.
    Usage: /save_character_data <path>
    """
    if len(arg) < 3:
        client.send_ooc("Filename must be at least 3 symbols long!")
        return

    try:
        path = 'storage/character_data'
        arg = f'{path}/{arg}.yaml'
        client.area.area_manager.save_character_data(arg)
        client.send_ooc(f'Saving as {arg} character data...')
    except AreaError:
        raise


@mod_only()
def ooc_cmd_load_character_data(client, arg):
    """
    Load the move_delay, keys, etc. for characters from a file in the storage/character_data/ folder.
    Usage: /load_character_data <path>
    """
    try:
        path = 'storage/character_data'
        arg = f'{path}/{arg}.yaml'
        client.server.area_manager.load_character_data(arg)
        client.send_ooc(f'Loading {arg} character data...')
    except AreaError:
        raise


def mod_keys(client, arg, mod=0):
    """
    A helper function to reduce copy-pasted code for /keys_(set|add|remove) commands.
    Modifies the keys of the target client/character folder/character id.
    :param arg: The arguments passed from the /keys_(set|add|remove) commands.
    :param mod: A number from 0-2 that dictates the operation. 0 = set, 1 = add, 2 = remove.
    """
    args = arg.split()
    if len(args) <= 1:
        raise ArgumentError("Please provide the key(s) to set. Keys must be a number 5 or a link eg. 1-5.")
    try:
        target = client.server.client_manager.get_targets(client, TargetType.ID, int(args[0]), False)
        if target:
            target = target[0].c_id
        else:
            if args[0] != '-1' and (int(args[0]) in client.server.char_list):
                target = int(args[0])
            else:
                try:
                    target = client.server.get_char_id_by_name(arg)
                except (ServerError):
                    raise
        args = args[1:]
        keys = []
        if mod == 1:
            keys = client.area.area_manager.get_character_data(target, 'keys', [])
        for a in args:
            for key in a.split('-'):
                # make sure all the keys are integers
                key = int(key)
            if not (a in keys):
                if mod == 2:
                    keys.remove(a)
                else:
                    keys.append(a)
        client.area.area_manager.set_character_data(target, 'keys', keys)
        client.send_ooc(f'Character folder {client.server.char_list[target]}\'s keys are updated: {keys}')
    except ValueError:
        raise ArgumentError('Keys must be a number like 5 or a link eg. 1-5.')
    except (AreaError, ClientError):
        raise


@mod_only()
def ooc_cmd_keys_set(client, arg):
    """
    Sets the keys of the target client/character folder/character id to the key(s). Keys must be a number like 5 or a link eg. 1-5.
    Usage: /keys_set <char> [key(s)]
    """
    if not arg:
        raise ArgumentError("Usage: /keys_set <char> [key(s)].")

    mod_keys(client, arg)


@mod_only()
def ooc_cmd_keys_add(client, arg):
    """
    Adds the keys of the target client/character folder/character id to the key(s). Keys must be a number like 5 or a link eg. 1-5.
    Usage: /keys_add <char> [key(s)]
    """
    if not arg:
        raise ArgumentError("Usage: /keys_add <char> [key(s)].")

    mod_keys(client, arg, 1)


@mod_only()
def ooc_cmd_keys_remove(client, arg):
    """
    Remvove the keys of the target client/character folder/character id from the key(s). Keys must be a number like 5 or a link eg. 1-5.
    Usage: /keys_remove <char>  [key(s)]
    """
    if not arg:
        raise ArgumentError("Usage: /keys_remove <char> [area id(s)]. Removes the selected 'keys' from the user.")

    mod_keys(client, arg, 2)


def ooc_cmd_keys(client, arg):
    """
    Check your own keys, or someone else's (if admin).
    Keys allow you to /lock or /unlock specific areas, OR
    area links if it's formatted like 1-5
    Usage: /keys [target_id]
    """
    args = arg.split()
    if len(args) < 1:
        client.send_ooc(f'Your current keys are {client.keys}')
        return
    if not client.is_mod:
        raise ClientError('Only mods can check other people\'s keys.')
    if len(args) == 1:
        try:
            target = client.server.client_manager.get_targets(client, TargetType.ID, int(args[0]), False)
            if target:
                target = target[0].c_id
            else:
                if args[0] != '-1' and (int(args[0]) in client.server.char_list):
                    target = int(args[0])
                else:
                    try:
                        target = client.server.get_char_id_by_name(arg)
                    except (ServerError):
                        raise
            keys = client.area.area_manager.get_character_data(target, 'keys', [])
            client.send_ooc(f'Target\'s current keys are {keys}')
        except:
            raise ArgumentError('Target not found.')
    else:
        raise ArgumentError("Usage: /keys [target_id].")