import asyncio

from apify import Actor
from apify.consts import ActorEventTypes

def validate_or_raise_input(input):
    REQUIRED_INPUT_KEYS = ['dataset', 'rowFnc']
    for attribute in REQUIRED_INPUT_KEYS:
        if attribute not in input or input[attribute] is None:
            raise ValueError(f"Missing or None value for required input: {attribute}")

async def main():
    async with Actor:
        # Get the value of the actor input
        actor_input = await Actor.get_input() or {}
        validate_or_raise_input(actor_input)
        Actor.log.info(f'INFO: The input is: {actor_input}')

        # Get dataset by ID or by name
        try:
            dataset = await Actor.open_dataset(id=actor_input["dataset"])
        except:
            dataset = await Actor.open_dataset(name=actor_input["dataset"])


        # Parse string fce from input to python fce
        row_function_code = compile(actor_input["rowFnc"], "<string>", "exec")
        exec(row_function_code)
        process_row_function_name = list(locals()).pop()

        # Save state in case Actor migrated or Aborted
        actor_state = await Actor.get_value('STATE_OFFSET')
        offset = 0
        if actor_state is not None:
            offset = actor_state
        # Save the state when the `PERSIST_STATE` event happens
        async def save_state(event_data):
            nonlocal offset
            Actor.log.info('Saving actor state', extra=event_data)
            await Actor.set_value('STATE', offset)
        Actor.on(ActorEventTypes.PERSIST_STATE, save_state)
        Actor.on(ActorEventTypes.ABORTING, save_state)

        # Loop though dataset items
        while True:
            dataset_item_list = await dataset.get_data(offset=offset, limit=1000)
            if len(dataset_item_list.items):
                break
            for line in dataset_item_list.items:
                offset = offset + 1
                try:
                    new_line = locals()[process_row_function_name](line)
                    await Actor.push_data(new_line)
                except Exception as err:
                    print(f'ERROR: Cannot process row, error: {err}')

        Actor.log.info('The actor finished, all lines processed.')
