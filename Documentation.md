# Machina ETL Pipeline
## Running the code
### Requirements
Before running, make sure you have all the requirements specified in the `environment.yml`. You can do this by creating a conda environment via running `conda env create --file=environment.yml`, and then activating this environment with the command `conda activate mkeller-solution`. The code can then be run by running `python run_pipeline.py`. 

### Run Options
There are 3 different ways to run the included pipeline, with different outputs. Running it plain as `python run_pipeline.py` will output runtime statistics, adding keyword `full` with `python run_pipeline.py full` will output a large csv with all metrics in one place, and inputting keyword `separate` like so: `python run_pipeline.py separate` will output a few different files each with their own metrics. See more [below](#output).

## Process and Solution
Here are some notes on what I did, and why I did it that way.

### Interpolation
The first real challenge was thinking about a way to fill missing values in a way that remains reasonable to the data at hand. I opted for linear time-based interpolation on the position data, and a backfill then forwardfill on the force data. 

My reasoning is that in travelling from A to B, the robot will travel through all intermediate points. In the absence of any extra information, it's best to assume a uniform velocity in the period between recorded points. This leaves metrics like velocity and distance travelled consistent with our best information.

As for force, it is harder to know how this might vary between known measurements. I opted to simply use data we had for nearby times. More on this [below](#ground-truth).

### Output
I provided program output in 3 formats. One is a single large csv stored in `output/{uuid}/full.csv`. This includes all known features, both measured and computed. Following instructions from README [2.2](README.md#22-convert-timeseries-to-a-wide-format) and [2.3](README.md#23-include-engineeredcalculated-features). You can get this by running `run_pipeline.py` with input keyword `full`.

A wide format and computed features can also be output as individual files by running `run_pipeline.py` with input keyword `separate`. This will output `wide.csv`, `motion.csv` and `vector_lengths.csv` to an`output/{uuid}` directory. This will contain a pivoted table, calculated robot movement, and normalized absolute value information respectively.

In addition to the above detailed data, simply running `run_pipeline.py` without any input will generate a runtime stats table at `output/runtime_stats.csv` as per [2.4](README.md#24-calculate-runtime-statistics)

### Python
I opted to use a simply python-pandas solution, for ease of use and quick coding. It isn't particularly performant, but allows for a quick solution on my end so I could focus on the data itself. More on this [below](#infrastructure). 

### Modularity
Following tips and suggestions from the provided instructions, the implemented solution is highly modular, and allows flexibility for changing requirements and leaves space open for changing metrics down the line. This is particularly relevant for any potential for future proofing a data process in a quick moving startup.

## Further Thoughts
Some things occurred to me while working on this problem about what an actually implemented production solution ought to look like, and what considerations to account for in creating this and similar pipelines to run on actual production data.

### Doing it live
The included pipeline compute metrics  on top of the raw data. Metrics such as velocity, acceleration, distance traveled, absolute force. These are both useful to live monitoring of the robots, and may be worth computing and recording alongside the data as it streams in.

### Ground Truth
While considering what approach to adopt in interpolating force and position data, I realized how important domain expertise would be to all the data manipulation and pipeline creation at Machina. I think it would be vital to discuss data process with the robotics engineers and metallurgists to get their thoughts on what makes the most sense, and discuss any hidden assumptions in the data pipeline process.

Furthermore, this is a highly real world problem, and the data is close and relevant to a ground truth reality. In contrast to some more typical data, here the analysis of our data will be in a tight feedback loop with a real world machine. This has significant impact on choices made along the way in the data processing infrastructure.

Proximity to a ground truth system cuts both ways here. On the one hand, it demands conversation with domain experts. On the other, it means that there are gaps in the data which need to be massaged. My role will not simply consist of facilitating data infrastructure, but also in translating back and forth between the machines and the machinists. 

### Monitoring and Validation
Something I mostly overlooked in my pipeline is checking the data for consistency, accuracy and type security. In practice, monitoring and reporting will play a significant and vital role to a healthy data infrastructure. In particular keeping in mind the [above discussion about groudn truth](#ground-truth). That is, we should be able to quickly identify something like a buggy sensor.

Of note here is the way in which even the provided sample data is incomplete. Most timestamps only contain one or another flavor of data, and some runs are missing some or even most metrics. While there's some amount of expected inconsistency, it's prudent to produce metrics on how much data is present vs absent.

Another concern is the type security inside the pipelines. Ensuring that unspoken assumptions are being checked as the data is in motion. This in particular is something which Scala is a much more efficient and natural solution for. As discussed [elsewhere](#infrastructure) in this document, I opted out of the kind of infrastructure-heavy approach for this homework that Scala would entail.

### Scaling
The first thing that was readily apparent is that while a few minutes of data from a handful of robots is quite manageable, this problem can quickly become a real burden to work with. In practice, we'll need to introduce a whole host of methods in order to facilitate efficient data operations.

A first step in this pipeline would be to time each function and see where the chokepoints are. I suspect that the original pivot is quite expensive in particular. 

Beyond that, even simple storage and retrieval is enough to demand special solutions here. I think every part fo this process ends up looking quite different. The provided pipeline can perhaps be ok for small scale ad-hoc analysis of a few minutes of data, but every part of this piepline would totally fail at any real scale.

### Infrastructure
The way I implemented this pipeline was with a focus on making it portable, flexible and lightweight, something that can be quickly spun up, iterated on and shared. This also matches the size of the data, which isn't very much. Production will be very different, we would want to introduce quite an elaborate system to facilitate the heavy lifting that we'll be demanding of our code.

In particular, while my solution is in pandas, we would definitely want to use spark to run our production pipelines. Enabling something like a cloud process with containerization, a Scala engine, pipeline orchestration and custom internal APIs. All this is the kind of work that requires rolling up sleeves and digging in, but pays off in the long run, which is what I'd be doing in Machina's production systems.