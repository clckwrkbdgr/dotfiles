from src.engine import events, actors, Events

events.Events.on(Events.Welcome)(lambda _:'Welcome!')
events.Events.on(Events.WelcomeBack)(lambda _:'Welcome back!')
events.Events.on(Events.NothingToPickUp)(lambda _:'Nothing to pick up here.')
events.Events.on(Events.InventoryIsFull)(lambda _: "Inventory is full! Cannot pick up {item}".format(item=event.item.name))
events.Events.on(Events.GrabItem)(lambda _:'{0} picks up {1}.'.format(_.actor.name, _.item.name))
events.Events.on(Events.InventoryIsEmpty)(lambda _:'Inventory is empty.')
events.Events.on(Events.NotConsumable)(lambda _:'Cannot consume {0}.'.format(_.item.name))
events.Events.on(Events.DropItem)(lambda _:'{0} drops {1}.'.format(_.actor.name.title(), _.item.name))
@events.Events.on(Events.BumpIntoTerrain)
def bumps_into_terrain(event):
	if not isinstance(event.actor, actors.Player):
		return "{Who} bumps.".format(Who=event.actor.name.title())
events.Events.on(Events.Move)(lambda _:None)
events.Events.on(Events.Health)(lambda _:'{0} {1:+}hp.'.format(_.target.name, _.diff))
events.Events.on(Events.BumpIntoActor)(lambda _:'{0} bumps into {1}.'.format(_.actor.name.title(), _.target.name))
events.Events.on(Events.Attack)(lambda _:'{0} hits {1} for {2}hp.'.format(_.actor.name.title(), _.target.name, _.damage))
events.Events.on(Events.StareIntoVoid)(lambda _:'The void gazes back.')

@events.Events.on(Events.Discover)
def on_discover(event):
	if hasattr(event.obj, 'name'):
		return '{0}!'.format(event.obj.name)
	else:
		return '{0}!'.format(event.obj)

@events.Events.on(Events.AutoStop)
def stop_auto_activities(event):
	if isinstance(event.reason[0], src.engine.actors.Actor):
		return 'There are monsters nearby!'
	return 'There are {0} nearby!'.format(', '.join(map(str, event.reason)))

@events.Events.on(Events.Death)
def monster_is_dead(_):
	if isinstance(_.target, actors.Player):
		return 'You died!!!'
	return '{0} dies.'.format(_.target.name.title())

events.Events.on(Events.Ascend)(lambda event:"Going up...")
events.Events.on(Events.Descend)(lambda event:"Going down...")
events.Events.on(Events.CannotDescend)(lambda event:"Cannot dig through the ground.")
events.Events.on(Events.CannotAscend)(lambda event:"Cannot reach the ceiling from here.")
events.Events.on(Events.ConsumeItem)(lambda event:"{actor} consumed {item}.".format(actor=event.actor.name.title(), item=event.item.name))

events.Events.on(Events.NotWielding)(lambda event:"Already wielding nothing.")
events.Events.on(Events.Unwield)(lambda event:"{actor} unwields {item}.".format(actor=event.actor.name.title(), item=event.item.name))
events.Events.on(Events.Wield)(lambda event:"{actor} wield {item}.".format(actor=event.actor.name.title(), item=event.item.name))
events.Events.on(Events.NotWearable)(lambda event:"Cannot wear {item}.".format(actor=event.actor.name.title(), item=event.item.name))
events.Events.on(Events.NotWearing)(lambda event:"Already wearing nothing.")
events.Events.on(Events.TakeOff)(lambda event:"{actor} takes off {item}.".format(actor=event.actor.name.title(), item=event.item.name))
events.Events.on(Events.Wear)(lambda event:"{actor} wears {item}.".format(actor=event.actor.name.title(), item=event.item.name))

del globals()['Events'] # FIXME to prevent namespace pollution in the main module
