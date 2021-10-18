# pokeemerald warp randomizer

Randomizes the warps in a stock pokeemerald repo.

## Usage Instructions
 - Install `networkx` and `matplotlib` via pip3 or similar.
 - Set `POKEEMERALD` environment variable to the path to your `pokeemerald/` folder
 - Edit `rand_idx` at the top of the file to the seed to start searching from.
 - **Ensure that the repo has not already been randomized, or the script will not work!**
 - `python3 randomizer.py`
 - The script will search for randomized layouts which pass completability tests. This can take anywhere from a couple of minutes to an hour.
   - "Completable" is defined as a series of pathfinding routes from the first gym to the last gym to the Elite 4, including required story events and in-order. As such, it is highly likely that sequence breaks will allow faster completion. The pathfinding routes do not use Cut, Fly nor the bikes.
   - Current average amount of viable generated seeds is about 1 in 20,000.
 - After a seed is found, map JSONs will be modified and `pokeemerald` can be compiled

## Notes
There are no guarantees on softlocking prevention, though several precautions are taken:
 - Littleroot Town is frozen to guarantee the player gets a Pokemon.
 - The Elite 4 are all frozen to enforce gym completion (but may be configurably unfrozen later?).
 - Petalburg Woods is currently frozen, but may be unfrozen later.
 - Mossdeep City Gym is frozen, due to complexity with verifying the puzzle can be completed with warps altered.
 - Petalburg Gym is frozen, due to doors being tied to trainers (high softlock potential).
 - Shoal Cave is frozen due to tides.
 - Trick House is frozen to prevent breakage.
 - Trainer Hill is frozen to prevent breakage.
 - Regi Tombs are frozen due to the Braille wall (but may be unfrozen later?).
 - The Mt. Chimney Cable Car is not randomized and will always travel between stations (the entrances and exits, however, are randomized).
 
## Pathfinding Structure
 - By default, all warps are connected bidirectionally to a central node (ie, `MAP_PETALBURG_CITY_WARP0..N` will connect to `MAP_PETALBURG_CITY`)
 - Connections are a bidirectional edge between central map nodes (ie, `MAP_PETALBURG_CITY` <-> `MAP_ROUTE102`)
 - For maps with ledges, edges can be cut in either direction.
 - Maps with partitioning generally forgo the central node and connect warps directly to each other.
 - Edges which require HMs or story flags will have an additional attribute `requires`, and during the completion tests these edges are cut if flags haven't yet been obtained.
