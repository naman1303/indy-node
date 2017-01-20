from copy import deepcopy

import pytest
from plenum.common.eventually import eventually
from plenum.common.txn import VERSION, NAME
from plenum.common.util import randomString

from sovrin_common.txn import SHA256, ACTION, CANCEL
from sovrin_node.test.upgrade.helper import bumpVersion, checkUpgradeScheduled, \
    ensureUpgradeSent


def testDoNotScheduleUpgradeForALowerVersion(looper, tconf, nodeSet,
                                             validUpgrade, trustee,
                                             trusteeWallet):
    """
    A node starts at version 1.2 running has scheduled upgrade for version 1.5
    but get a txn for upgrade 1.4, it will not schedule it. To upgrade to 1.4,
    send cancel for 1.5
    """
    upgr1 = deepcopy(validUpgrade)

    upgr2 = deepcopy(upgr1)
    upgr2[VERSION] = bumpVersion(upgr1[VERSION])
    upgr2[NAME] += randomString(3)
    upgr2[SHA256] = randomString(32)

    # An upgrade for higher version scheduled, it should pass
    ensureUpgradeSent(looper, trustee, trusteeWallet, upgr2)
    looper.run(eventually(checkUpgradeScheduled, nodeSet, upgr2[VERSION],
                          retryWait=1, timeout=5))

    # An upgrade for lower version scheduled, the transaction should pass but
    # the upgrade should not be scheduled
    ensureUpgradeSent(looper, trustee, trusteeWallet, upgr1)
    with pytest.raises(AssertionError):
        looper.run(eventually(checkUpgradeScheduled, nodeSet, upgr1[VERSION],
                              retryWait=1, timeout=5))

    # Cancel the upgrade with higher version
    upgr3 = deepcopy(upgr2)
    upgr3[ACTION] = CANCEL
    ensureUpgradeSent(looper, trustee, trusteeWallet, upgr3)

    # Now the upgrade for lower version should be scheduled
    looper.run(eventually(checkUpgradeScheduled, nodeSet, upgr1[VERSION],
                          retryWait=1, timeout=5))
