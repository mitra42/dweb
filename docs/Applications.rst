.. _Applications:

************
Applications
************

* <these are just notes>
* Need to defined some example applications here, e.g. using Wordpress and Facebook as examples
* From Facebook, consider: FaceBook; including: Identity; Profile; Timeline; NewsFeed; Likes; Comments; Shares; Groups; Events; Privacy;
* Personal Homepage
* Wordpress: Layout; Items;
* WikiLeaks
 * Corporate web page
* Distributed Email (probably doesnt make sense)



A general exploration of how to do Facebook on Web4.2

Depends on:
Depended on by:

Facebook consists of:
     My profile, info about me
     My friend graph
     My timeline
     My events
     Each of the above, by other people
     Likes
     Shares
     Comments
     Groups - with permissions and revokable membership and moderators
     Privacy

These could be broken out into individual Evernotes if reqd

FB:Identity would be a UniqueID
FB:Profile: An object containing MetaData about me
     ? How to control who sees what fields of that data and how to make control of that trivial see FB:Privacy
FB:FriendGraph
     A SignedList of other people’s FBIdentity signed by me.
     Tag use undefined but could add complexity like Google Circles etc, or meta-data about relationship.
     Tags used to support whose FB:TimeLine ends up on my FB:NewsFeed.
     SignedList supports deletion

FB:Timeline
     A SignedList includes date of posting, and an Object
     Each object in the list would be JSON and could be for example a status update.
     SignedList supports deletion
     Each object can have a response SignedList for FB:Likes & FB:Comments

FB:Like
     A Like is an entry on the response SIgnedList of, for example, an object in a FB:Timeline
     It would have tag=Like; PubKey=Liker’s Pubkey;
     Note that we can retrieve the PubKey to get the Liker’s FB:Identity.
     It might, or might not, also be an entry in the Liker’s FB:Timeline
     It is signed by the Liker, not be the Likee
     It can be removed by either Liker or Likee with a later signed entry
          (note that removal wouldn’t remove from Liker’s timeline, only from Likee’s Response List).

FB:Comment
     Is similar to a FB:Like but would have an associated Object,
     the rules of what was allowed in these sub-objects is up to FB.

FB:Share
     is an object on my FB:Timeline that refers to another object,

FB:Newsfeed
     The stream of things on my friends timelines.
     Runs a query for each of my FB:FriendGraph,
          finds (cacheable) their FB:Timeline;
               retrieves everything in it since some Date.
     Sorts results into Date order or whatever other priority is application determined.
     Allows for any kind of intelligence in the app determining what to show me.

FB: Event
     Is a SignedList of objects made up of calendar MetaData

FB:Group
     Groups are more complex,
     A group probably needs a (distributed) GroupApp controlled by its moderators.
     A group’s data includes which FB:Identity are moderators and allowed to sign.
     The GroupApp controls a PubKey/PrivKey pair
     The FB:Group:MembershipList is a SignedList (by the app)
     The FB:Group:Timeline is a SignedList (signed by FB:GroupApp)
     To post, a member adds to a Request List,
     For a members-only posting, the FB:GroupApp checks new entries on this Request List
          against the FB:GroupMembership, and copies with signature to FB:Group:TimeLine
     If posts are moderated, then it could be moderators who watch this list and sign.
     Any levels of rules can be built into the FB:GroupApp, or into a DistributedObject with FB:GroupApp rules.
     I’ve done some work elsewhere on distributed permission lists on pub keys - to be found

FB:Privacy
     More thinking needed on how to control who sees what and requiring encryption

Facebook FB