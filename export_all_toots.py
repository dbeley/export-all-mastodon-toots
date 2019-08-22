import configparser
import pandas as pd
import argparse
from pathlib import Path
import logging
import time
from mastodon import Mastodon

logger = logging.getLogger()
temps_debut = time.time()
config = configparser.ConfigParser()
config.read("config.ini")


def mastodonconnect():
    if not Path("mastodon_clientcred.secret").is_file():
        Mastodon.create_app(
            "mastodon_bot_lastfm_cg",
            api_base_url=config["mastodon"]["api_base_url"],
            to_file="mastodon_clientcred.secret",
        )

    if not Path("mastodon_usercred.secret").is_file():
        mastodon = Mastodon(
            client_id="mastodon_clientcred.secret",
            api_base_url=config["mastodon"]["api_base_url"],
        )
        mastodon.log_in(
            config["mastodon"]["login_email"],
            config["mastodon"]["password"],
            to_file="mastodon_usercred.secret",
        )

    mastodon = Mastodon(
        access_token="mastodon_usercred.secret",
        api_base_url=config["mastodon"]["api_base_url"],
    )
    return mastodon


def process_status(status):
    toot = {}
    toot["text"] = status["content"]
    toot["reblogs"] = status["reblogs_count"]
    toot["favorites"] = status["favourites_count"]
    toot["replies"] = status["replies_count"]
    toot["date"] = str(status["created_at"])
    toot["name"] = status["account"]["username"]
    toot["screen_name"] = status["account"]["display_name"]
    toot["url"] = status["url"]
    try:
        toot["media"] = status.entities["media_attachments"][0]["url"]
    except Exception as e:
        logger.debug(e)
    return toot


def main():
    args = parse_args()
    list_users = [x.strip() for x in args.user.split(",")]
    toots = []
    Path("Exports").mkdir(parents=True, exist_ok=True)
    mastodon = mastodonconnect()

    for user in list_users:
        user_id = mastodon.account_search(user)[0]["id"]
        page = mastodon.account_statuses(id=user_id)
        index = 1
        while True:
            if page:
                logger.info("Page present.")
                for status in page:
                    logger.info("Extracting toot %s for %s.", index, user)
                    if args.export_retweets:
                        toots.append(process_status(status))
                    else:
                        # If not retweet
                        if not status["reblog"]:
                            toots.append(process_status(status))
                        else:
                            logger.info("Status is a retweet. Skipping.")
                    index += 1
                min_id = min([int(x["id"]) for x in page])
                logger.info("min_id : %s.", min_id)
                page = mastodon.account_statuses(id=user_id, max_id=min_id)
            else:
                logger.info("Page not present.")
                break

        df = pd.DataFrame.from_records(toots)
        print(df.head())

        writer = pd.ExcelWriter("Exports/export_" + str(user) + ".xlsx")
        df.to_excel(writer, "Sheet1", index=False)
        writer.save()
    logger.info("Runtime : %.2f seconds." % (time.time() - temps_debut))


def parse_args():
    format = "%(levelname)s :: %(message)s"
    parser = argparse.ArgumentParser(
        description="Export all toots for one or several mastodon accounts."
    )
    parser.add_argument(
        "--debug",
        help="Display debugging information.",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
        default=logging.INFO,
    )
    parser.add_argument(
        "-u", "--user", type=str, help="Username (separated by comma)."
    )
    parser.add_argument(
        "-r",
        "--export_retweets",
        help="Export retweets (default = False).",
        dest="export_retweets",
        action="store_true",
    )
    parser.set_defaults(export_retweets=False)

    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel, format=format)
    return args


if __name__ == "__main__":
    main()
