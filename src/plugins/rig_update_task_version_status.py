# 2021, Chris Crocetti

import os


def registerCallbacks(reg):
    """
    Register our callbacks
    :param reg: A Registrar instance provided by the event loop handler
    """

    # Grab authentication env vars for this plugin. Install these into the env
    # if they don't already exist.
    # script_name = os.environ["SGDAEMON_SGJIRA_NAME"]
    # script_key = os.environ["SGDAEMON_SGJIRA_KEY"]
    script_name = "sgdaemon"
    script_key = "jwbveS4r*fqgqsazpbyhtsktq"

    # Define the filter on versions
    # args = [
    #     ["sg_task.Task.step.Step.code", "is", "Rigging"],
    # ]
    args = []

    reg.registerCallback(
        script_name,
        script_key,
        version_status_changed,
        {"Shotgun_Version_Change": ["sg_status_list"]},
        args,
    )
    reg.logger.debug("Registered callback.")


def version_status_changed(sg, logger, event, args):
    """
    When a Rigging Version is set to apr, updated the latest Publish
    to Complete, and set all existing cmpt Publishes to ip (or vwd).

    :param sg: Shotgun API instance
    :param logger: Standard Event loop logger
    :param event: ShotgunEvent this trigger is listening for
    :param args: Additional arguments registerd for this trigger.
    """

    # Check if Version is Rigging and is set to Approved.
    entity = event.get("entity", {})
    if not entity or entity == {}:
        return
    if event['meta']['new_value'] != "apr":
        return
    ver = sg.find_one("Version", [["id", "is", entity['id']],
                                  ["sg_task.Task.step.Step.code", "is", "Rigging"],
    ])
    if not ver:
        return

    print("*** Rigging version set to Complete", entity['id'])
    return

    # TODO: Once turntable tool is completed, do request to get associated PublishedFiles.
    # TODO: May be a single file, may be multiple.

    # Get all PublishedFiles, sorted by date, descending.
    # TODO: Field not installed.
    published_files = []

    # Set latest to Complete.
    pid = published_files[0]['id']
    sg.update("PublishedFile", pid, {'sg_status_list': 'apr'})

    # Set others to IP / VWD if Complete.
    batch_cmds = []
    for i in published_files[1:]:
        if published_files[i]['sg_status_list'] == 'apr':
            batch_cmds.append(
                {
                    "request_type": "update",
                    "entity_type": "PublishedFile",
                    "entity_id": published_files[i]['id'],
                    "data": {"sg_status_list": 'ip'},
                }
            )

    # Execute update.
    if batch_cmds:
        # Execute the batch command(s)
        logger.info(
            "Running [%d] batch command(s) to update PublishedFile values ..."
            % (len(batch_cmds))
        )
        [logger.debug("    %s" % bc) for bc in batch_cmds]
        results = sg.batch(batch_cmds)
        logger.debug("    RESULTS: %s" % results)

    