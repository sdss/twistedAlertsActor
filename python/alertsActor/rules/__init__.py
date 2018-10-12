
import click

from functools import update_wrapper


def pass_actor(f):
    # Unpacks the context and send the actor.
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        print(ctx.get_help())
        return ctx.invoke(f, ctx.obj['actor'], *args, **kwargs)
    return update_wrapper(new_func, f)
