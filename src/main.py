import asyncio

from apify import Actor

async def main():
    async with Actor() as actor:

        # Get the value of the actor input
        actor_input = await actor.get_input()

        print(f'INFO: The input is: {actor_input}')

        dataset = await actor.open_dataset(actor_input["dataset"])

        row_function_code = compile(actor_input["rowFnc"], "<string>", "exec")
        exec(row_function_code)
        process_row_function_name = list(locals()).pop()

        dataset_item_list = await dataset.get_data()

        for line in dataset_item_list.items:
            try:
                new_line = locals()[process_row_function_name](line)
                await actor.push_data(new_line)
            except Exception as err:
                print(f'ERROR: Cannot process row, error: {err}')

        print('INFO: The actor finished, all lines processed.')

# Run the main function of the script, if the script is executed directly
if __name__ == '__main__':
    asyncio.run(main())
