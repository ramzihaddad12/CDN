## High Level Approach:

Starting the project, my partners and I read through the Raft paper and watched a few YouTube videos on how the algorithm worked. Once we had a better understanding, we began implementing the code by mostly following the guidlines of the paper. This was easier said than done, however, as the complexity of the algorithm often seemed overwhelming and led to a lot of confusion along the way. Nonetheless, we kept getting a better understanding every time we failed.

## Challenges we faced:

As I alluded to in the previous paragraph, designing a distributed system was very difficult for us. Although the Raft paper gave us almost everything we could need, it felt as if there were so many conditionals to deal with that it was often easy to get lost. Although making it through the election logic with relative ease, we faced major difficulty with implementing the log replication. This mostly came from overcomplicating things due to a lack of understanding; to start, my team and I implemented batched entries which was great, but it made the logic a bit more complicated. Also, although unrelated to the project, we were all extremely fatigued from a semester of work and added pressure from finals. This made us work slower and more prone to making mistakes.

## Properties/features of the design that’s good:

Something that we did very well was separating the logic into different classes. As an example, we had a Candidate, Follower, and a Leader class which all had different ways of handling the same events like a timeout occuring. This just made for easier code to read and modify. Also, we put a heavy emphasis on decoupling code by using constants wherever we could and using abstract classes for shared functionality (between candidates and followers).

## Overview of how the code was tested:

Mostly, the code was tested against the provided config files; however, we also wrote some test functions to validate various logic.

## Unit Testing the Code

For running all of the tests within the "tests" module:
`python -m unittest discover tests`

For running all of the tests within a file in the "tests" module
`python -m unittest tests.test_follower`

### Helpful Commands

`zip p6.zip 3700kvstore Makefile README.md networks/* -x networks/__pycache__`
