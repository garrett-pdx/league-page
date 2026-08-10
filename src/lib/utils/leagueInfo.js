/*   STEP 1   */
export const leagueID = "1312235880743706624"; // your league ID
export const leagueName = "The Mudd League"; // your league name (Sleeper calls it "Mudd Keeper League")
export const dynasty = false; // true for dynasty leagues, false for redraft and keeper
export const enableBlog = false; // requires VITE_CONTENTFUL_ACCESS_TOKEN and VITE_CONTENTFUL_SPACE environment variables

/*   STEP 2   */
export const homepageText = `
  <p>Ten teams. Half-PPR. Two keepers each, and a long memory.</p>
  <p>The Mudd League has been running since 2022. It's a keeper league, not a dynasty league &mdash; every fall the whole pool goes back on the board except the two players each manager decides are worth holding onto. Holding one isn't free: a keeper costs you the round you drafted him in last year, and if you keep the same player two years running, that cost climbs a round. Good players get expensive. That's the point.</p>
  <p>Starters are QB, two RB, two WR, TE and two FLEX, with six on the bench and two IR spots. Waivers run on a $100 FAAB budget, the trade deadline is week 12, and the top four teams make a playoff that kicks off in week 16.</p>
  <p>Working out who to keep? The <a href="https://garrett-pdx.github.io/keeper-draft-board/" target="_blank" rel="noopener">Keeper Draft Board</a> does the round math for you, shows what everyone else has locked in, and runs the draft itself.</p>
  <p><strong>malstol</strong> is the reigning champion. Everyone else has eleven months to do something about it.</p>
`;

/*   STEP 3   */
/*
The ten current managers, keyed by their Sleeper managerID (user_id).

TODO: `name` and `bio` are still placeholders -- `name` is each manager's Sleeper handle
and `bio` is a stub. Swap in real names and write bios.

`photo` points at a LOCAL file in /static/managers/, named after the manager's Sleeper
handle. These started life as each manager's own Sleeper avatar but are now served by us,
which is deliberate: the sleepercdn URL embeds a content hash, so hotlinking it broke the
moment a manager changed their avatar. Files are named by handle, not by display name, so
renaming a manager doesn't orphan their photo.

Most are .webp (that's what Sleeper serves); gurret is .jpg. Check the actual bytes before
trusting an extension -- Sleeper's Content-Type header lies, it returned "image/png" for a
file that was really JPEG. To refresh one, re-download it and keep the extension honest.

Note two upstream traps before you edit these:
  - `photo` and `rival` are NOT optional despite the docs below saying fields can be
    nulled. Both are rendered unguarded, and omitting `rival` throws on the manager
    detail page. Keep a value in each.
  - `rival.link` is an index into THIS array, so it shifts if you reorder the entries.
    null links back to the all-managers page.
*/

export const managers = [
    {
      "managerID": "76909640692416512",
      "name": "Garrett Cheadle",
      "location": "Portland, OR",
      "photo": "/managers/gurret.jpg",
      "bio": "<strong>#24 &middot; RB &middot; 6'0&quot; &middot; 215 lbs &middot; Lincoln HS</strong><br /><em>CMS career: 36 G &middot; 17 GS &middot; 588 car &middot; 2,987 yds &middot; 33 rush TD &middot; 5.1 avg &middot; 26 rec, 228 yds, 1 TD &middot; 204 pts</em><br />Commissioner. Third all-time at Claremont-Mudd-Scripps in both rushing yards and rushing touchdowns. SCIAC Offensive Player of the Year and First-Team All-SCIAC as a junior in 2018, when he carried 245 times for 1,305 yards at 118.6 a game and set the program single-game record with 274 against Whittier. Came back for 763 yards and a career-best 11 touchdowns as a senior despite a midseason injury, adding Second-Team All-SCIAC, the National Football Foundation Hampshire Honors Society and the SCIAC All-Academic Team. Son of Jim and Maria Cheadle.",
      "rival": {
        name: "The Field",
        link: null,
        image: "/managers/everyone.png",
      },
    },
    {
      "managerID": "611697269254791168",
      "name": "Tyson-Jay Saena",
      "location": "Chandler, AZ",
      "photo": "/managers/tnt44.webp",
      "bio": "<strong>#44 &middot; DL &middot; 5'11&quot; &middot; 260 lbs &middot; Hamilton HS</strong><br /><em>CMS career: 36 G &middot; 14 GS &middot; 68 tackles &middot; 6 TFL for 17 &middot; 2 sacks for 11 &middot; 2 FR &middot; 1 FF</em><br />Defensive lineman whose CMS career ran from 2016 all the way to 2022, with a two-year absence in the middle that he returned from to play all ten games in 2019. Second-Team All-SCIAC in each of his final two seasons, and as a senior he recorded at least one tackle in every game he played. Opened 2021 with three tackles and a sack against Pomona-Pitzer. Sings and plays the ukulele. Son of Allan and Joyce Saena.",
      "rival": {
        name: "The Field",
        link: null,
        image: "/managers/everyone.png",
      },
    },
    {
      "managerID": "605683461667229696",
      "name": "Michael Streinz",
      "location": "Portland, OR",
      "photo": "/managers/mikestreinz.webp",
      "bio": "<strong>#74 &middot; OL &middot; 6'3&quot; &middot; 265 lbs &middot; Wilson HS</strong><br /><em>CMS career: offensive line, so the stat sheet is blank on principle</em><br />Guard, and the league's second Portlander. Started all ten games in 2019 on a line that led the nation in time of possession and averaged 199.7 rushing yards a game &mdash; including back-to-back afternoons of 376 and 393 on the ground against Occidental and Whittier, and 220 yards with 40:44 of possession to take the Sixth Street Trophy off Pomona-Pitzer. Which is another way of saying a good many of Garrett Cheadle's yards came out from behind him. National Football Foundation Hampshire Honors Society, twice SCIAC All-Academic, and a high school valedictorian. Son of Ray and Mary Streinz.",
      "rival": {
        name: "The Field",
        link: null,
        image: "/managers/everyone.png",
      },
    },
    {
      "managerID": "611664340277383168",
      "name": "Tucker Harris",
      "location": "Sarasota, FL",
      "photo": "/managers/tuckersdumbteam.webp",
      "bio": "<strong>#70 &middot; OL &middot; 6'1&quot; &middot; 235 lbs &middot; Out-of-Door Academy</strong><br />Arrived at Claremont-Mudd-Scripps as a running back wearing 35, lost his first year to a midseason injury, and came back as an offensive lineman wearing 70 &mdash; which is why his career stat page is gloriously blank. Second-Team All-Conference on the line as a high schooler in Sarasota. Data science major at Claremont McKenna, reads Orwell, admires Theodore Roosevelt.",
      "rival": {
        name: "The Field",
        link: null,
        image: "/managers/everyone.png",
      },
    },
    {
      "managerID": "870570674836656128",
      "name": "Paul Slaats",
      "location": "Malvern, PA",
      "photo": "/managers/paulslaats.webp",
      "bio": "<strong>#90 &middot; DL &middot; 6'3&quot; &middot; 265 lbs &middot; Great Valley HS</strong><br /><em>CMS career: 34 G &middot; 14 GS &middot; 154 tackles (64 solo) &middot; 22 TFL for 58 &middot; 6.5 sacks for 26 &middot; 1 FF &middot; 1 FR &middot; 1 blocked kick</em><br />Defensive lineman and 2016 team captain. Four years on the line, peaking with 46 tackles and 7.5 tackles for loss as a junior &mdash; the year he took SCIAC Athlete of the Year, Harvey Mudd Athlete of the Year and third-team All-West Region from D3Football.com. First-Team All-SCIAC the season before. Also managed a forced fumble, a fumble recovery and a blocked kick along the way. Son of Paul and Kathryn Slaats.",
      "rival": {
        name: "The Field",
        link: null,
        image: "/managers/everyone.png",
      },
    },
    {
      "managerID": "612407006212468736",
      "name": "Jonah Cartwright",
      "location": "Carmichael, CA",
      "photo": "/managers/jonahcartwright.webp",
      "bio": "<strong>#26 &middot; RB &middot; 5'9&quot; &middot; 195 lbs &middot; Rio Americano HS</strong><br /><em>CMS career: 23 G &middot; 100 car &middot; 286 yds &middot; 2 TD &mdash; and together with fellow Harvey Mudd running back Garrett Cheadle, he rushed for a combined 3,273 yards and 35 touchdowns</em><br />Running back and National Football Foundation Hampshire Honors Society selection. Waited three seasons for his carries and got them as a senior, going for 190 yards on the year &mdash; including a 27-carry, 101-yard afternoon against Occidental that produced both of his career touchdowns on the same day. Listed his favorite hobby as fantasy football, which by now reads as foreshadowing. Son of Scott and Alice Cartwright.",
      "rival": {
        name: "The Field",
        link: null,
        image: "/managers/everyone.png",
      },
    },
    {
      "managerID": "611630747161358336",
      "name": "Kevin Shoyer",
      "location": "Hingham, MA",
      "photo": "/managers/kshoyer.webp",
      "bio": "<strong>#14 &middot; DB &middot; 6'2&quot; &middot; 198 lbs &middot; Hingham HS</strong><br /><em>CMS career: 17 G &middot; 4 GS &middot; 35 tackles (22 solo) &middot; 7 TFL</em><br />Defensive back out of Hingham, Massachusetts. Appeared in all nine games as a freshman and put up 24 tackles, then went back out as a sophomore and piled up seven tackles for loss alongside a SCIAC All-Academic selection. Names his biggest sports moment as a 55-yard touchdown on the last play of a Thanksgiving Day game, which for a defensive back is showing off. Son of Lori and Tim Shoyer.",
      "rival": {
        name: "The Field",
        link: null,
        image: "/managers/everyone.png",
      },
    },
    {
      "managerID": "999190763323944960",
      "name": "Brenden Brown",
      "location": "Castro Valley, CA",
      "photo": "/managers/bbrown16.webp",
      "bio": "<strong>#16 &middot; QB &middot; 6'4&quot; &middot; 215 lbs &middot; Castro Valley HS</strong><br /><em>CMS career: 17 G &middot; 0 GS &middot; 32/59 (54.2%) &middot; 359 yds &middot; 4 TD &middot; 1 INT &middot; long 30</em><br />Quarterback and 2018 SCIAC All-Academic selection who appeared in 17 games across four years without ever starting one. Made them count: coming off the bench against Northwestern he threw two touchdown passes that accounted for every point CMS scored in a 14-3 win. Four career touchdown passes against a single interception. Finished up in the NCAA Tournament against Whitworth. Son of Mary Janatpour and Mark Brown.",
      "rival": {
        name: "The Field",
        link: null,
        image: "/managers/everyone.png",
      },
    },
    {
      "managerID": "611649934390870016",
      "name": "Kanoa Gilliland",
      "location": "Kaneohe, HI",
      "photo": "/managers/kabroa.webp",
      "bio": "<strong>#90 &middot; DL &middot; 6'0&quot; &middot; 200 lbs &middot; Kamehameha Kapalama</strong><br /><em>CMS career: 11 G &middot; 6 tackles &middot; 1 TFL for 7 &middot; 0.5 sacks &middot; 1 forced fumble</em><br />Defensive lineman, and the only manager in the league who had to cross an ocean to get to practice &mdash; Kaneohe, Hawaii by way of Kamehameha Kapalama. Forced a fumble across his eleven games on the line. Names his biggest sports moment as a scoop-and-score, which the CMS stat sheet politely declines to corroborate. Son of Beau and Judy Gilliland.",
      "rival": {
        name: "The Field",
        link: null,
        image: "/managers/everyone.png",
      },
    },
    {
      "managerID": "850475150817234944",
      "name": "Malcolm Stolarski",
      "location": "River Forest, IL",
      "photo": "/managers/malstol.webp",
      "bio": "<strong>#68 &middot; OL &middot; 6'4&quot; &middot; 250 lbs &middot; Oak Park &amp; River Forest HS</strong><br /><em>CMS career: four years on the line &middot; 1 tackle (2016, and he'd like it noted)</em><br />Reigning champion. Offensive tackle, which means the stat sheet credits him with exactly one tackle in four years and nothing else &mdash; the position's numbers live in everyone else's totals. Started every game as a true freshman on his way to Offensive Newcomer of the Year, started them all again in 2016 and 2017, and took Second-Team All-SCIAC along the way. Played all eleven games at tackle as a senior on a line that blocked for a certain Garrett Cheadle and finished second in the country in time of possession. Son of Michael Stolarski and Kim Steinke-Stolarski.",
      "rival": {
        name: "The Field",
        link: null,
        image: "/managers/everyone.png",
      },
    },
  ]


  /*   !!  !!  IMPORTANT  !!  !! */
  /*
  Below is the most up to-date version of a manager. Please leave this commented out
  and don't delete it. This will be updated if any fields are added, removed or changed
  and will allow updates without causing merge conflicts
  */

    // {
    //   "roster": 3,  // (DEPRECATED! Don't use this anymore) ID of the roster that the manager manages (look at the order of the power rankings graph)
    //   "managerID": "12345678",  // the user's manager ID, go to https://api.sleeper.app/v1/league/<your_league_id>/users to find user IDs (you can use older leagueIDs to find user IDs for managers that are no longer in the league)
    //   "name": "Your Name",
    //   "tookOver": 2020, // (DEPRECATED! You don't need to use this anymore) (optional) used if a manager took over a team, delete this line or change to null otherwise
    //   "location": "Brooklyn", // (optional)
    //   "bio": "Lorem ipsum...",
    //   "photo": "/managers/name.jpg", // square ratio recommended (no larger than 500x500)
    //   "fantasyStart": 2014, // (optional) when did the manager start playing fantasy football
    //   "favoriteTeam": "nyj", // (optional) favorite NFL team, (follows convention: nyj, sea, mia, etc.) MUST BE LOWERCASE
    //   "mode": "Win Now", // (optional) 'Win Now', 'Dynasty', or 'Rebuild' (anything else and you will need to add a new png to /static/ similar to the 'Rebuild.png' and 'Win Now.png' currently in there)
    //   "rival": {
    //     name: "Rival", // Can be anything (usually your rival's name)
    //     link: 6, // manager array number within this array, or null to link back to all managers page
    //     image: "/managers/rival.jpg", // either a specific manager photo or '/managers/everyone.png' or '/managers/question.png'
    //   },
    //   "favoritePlayer": 1426, // (optional) this corresponds to the Sleeper player ID (https://api.sleeper.app/v1/players/nfl)
    //   "valuePosition": "WR", // (optional) Favorite position (QB, WR, RB, TE, etc.)
    //   "rookieOrVets": "Rookies", // (optional) 'Rookies' or 'Vets' (anything else and you will need to add a new png to /static/ similar to the 'Rookies.png' and 'Vets.png' currently in there)
    //   "philosophy": "Your fantasy team's philosophy", // (optional)
    //   "tradingScale": 10, // 1 - 10 (optional)
    //   "preferredContact": "Text",  // (optional) 'Text', 'WhatsApp', 'Sleeper', 'Email', 'Phone', 'Discord', and 'Carrier Pigeon' are currently supplied in the template
    // },

