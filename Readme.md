# Controller Topology Project

"Topology" is the way in which things are connected. Connections appear in emulation in several ways. For example, buttons on modern controllers map to buttons on retro controllers.

As another example, SNES supports hubs called "multitaps". These allow four controllers to connect to a single port on the SNES console.

This project aims to curate connections like this for all gaming history.

For a practical example of what be done with this data, see the [visualization experiment](scripts).

## Data specification

This database is structed for Kodi. A future script might spit out XML, JSON or JSON-LD, to allow for database queries.

See [Readme-Addons.md](Readme-Addons.md) for the complete specification of how the data is stored.

## Topology types

Currently, this project uses two type of topologies:

### 1. Button topology

The button topology is how the buttons on controllers map to each other. To visualize this, imagine a SNES controller next to a 360 controller, with lines drawn from buttons on the SNES controller to the corresponding buttons on the 360 controller.

With this information, if a user is holding a 360 controller, we can automatically generate a buttonmap for SNES emulators.

### 2. Wire topology

The wire topology is how controllers are physically wired to the emulated game console. Two specific types of connections need to be modeled: multitaps and daisy chaining.

## Controller representations

The button topology allows for automatically mapping between controllers. This is done using controller "profiles", which describe the button and wire layout.

However, generating a profile typically requires the original controller. Blurry images on Google Image Search don't expose the information we need, unfortunately.

Furthermore, even if we could get our hands on every controller ever, we can't manually map every controller to every other controller. The amount of work explodes quadratically. We need an automated solution.

So how do we solve profile generation and buttonmap generation?

To solve these problems, we transform controller profiles into different "representations" that we have data for, curate data for that representation, then transform the data back into the controller profile.

### Libretro representation

Libretro emulators necessarily know which buttons are on their controllers. We curate button data from emulators for the libretro abstraction, then transform the data from the libretro abstraction back into our controller profiles.

Now, we have button data for most controllers.

### Driver representation

Many projects, including libretro and Kodi, curate data mapping driver button IDs to a controller profile. Kodi allows mapping a physical controller to multiple profiles. When multiple profiles are mapped to the same driver data, we can transform this data back into mappings between profiles.

Now, we have data mapping controllers to each other.
