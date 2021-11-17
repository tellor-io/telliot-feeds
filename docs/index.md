# Welcome to Telliot's documentation

## Overview


Telliot is a Python framework for interacting with the decentralized TellorX network.
With Telliot, you (or your smart contract) can:

* Ask the TellorX Decentralized Oracle to answer a question (we call that *tipping*)

* Submit answers to questions that other people (or smart contracts) ask. (we call that *reporting*.  Reporters earn tips, but must stake TRB
    as collateral against incorrect answers)

* Look up historical answers.

* Help maintain the security of the TellorX network by disputing inaccurate
  answers and voting on other disputes.

Of course, TellorX supports DeFi with questions such as "What is the
current price of Bitcoin in US Dollars?"  But that is just the beginning.
TellorX also supports arbitrary questions and answers.  Any question is OK, provided
that the Tellor community can answer it with a reasonable
degree of confidence (remember, Reporters may lose TRB if the network votes
the answer incorrect!)

## Telliot Software

The telliot software currently consists of two main python packages:

- [Telliot Core](https://github.com/tellor-io/telliot-core)
  - This package provides core functionality and a plugin framework for use
    by other Telliot subpackages and custom data feeds.

- [Telliot Feed Examples](https://github.com/tellor-io/telliot-feed-examples)
  - This package provides several working examples of data feeds that can be either customized
    or used directly.




## Scope

Telliot aims to make it easier to ask questions in a format that the Oracle
can understand, and specify the format (i.e. data structure) of the
answers you would like to receive - so that the community can answer
them more reliably.

The TellorX network is open to everyone, and Telliot is just
one way to access it.  You can use all of Telliot, parts of it, or not
use it at all.  You can also make contributions to improve it.


!!! warning
    Use Telliot at your own risk.  **It may have bugs!  Bugs may cost you real money!**
    If you find any, please [submit an issue](https://github.com/tellor-io/telliot-core/issues),
    or better yet [create a pull request](https://github.com/tellor-io/telliot-core/pulls)
    with a suggested fix.

