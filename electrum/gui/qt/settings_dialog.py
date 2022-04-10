#!/usr/bin/env python
#
# Electrum - lightweight Bitcoin client
# Copyright (C) 2012 thomasv@gitorious
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import ast
from typing import Optional, TYPE_CHECKING

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QComboBox,  QTabWidget,
                             QSpinBox,  QFileDialog, QCheckBox, QLabel,
                             QVBoxLayout, QGridLayout, QLineEdit,
                             QPushButton, QWidget, QHBoxLayout, QTextEdit)

from electrum.i18n import _, languages
from electrum import util, coinchooser, paymentrequest
from electrum.util import base_units_list

from electrum.gui import messages

from .util import (ColorScheme, WindowModalDialog, HelpLabel, Buttons,
                   CloseButton)


if TYPE_CHECKING:
    from electrum.simple_config import SimpleConfig
    from .main_window import ElectrumWindow


class SettingsDialog(WindowModalDialog):

    def __init__(self, parent: 'ElectrumWindow', config: 'SimpleConfig'):
        WindowModalDialog.__init__(self, parent, _('Preferences'))
        self.config = config
        self.window = parent
        self.need_restart = False
        self.save_blacklist = False
        self.save_whitelist = False
        self.fx = self.window.fx
        self.wallet = self.window.wallet
        
        vbox = QVBoxLayout()
        tabs = QTabWidget()
        gui_widgets = []
        tx_widgets = []
        oa_widgets = []
        asset_widgets = []

        # language
        lang_help = _('Select which language is used in the GUI (after restart).')
        lang_label = HelpLabel(_('Language') + ':', lang_help)
        lang_combo = QComboBox()
        lang_combo.addItems(list(languages.values()))
        lang_keys = list(languages.keys())
        lang_cur_setting = self.config.get("language", '')
        try:
            index = lang_keys.index(lang_cur_setting)
        except ValueError:  # not in list
            index = 0
        lang_combo.setCurrentIndex(index)
        if not self.config.is_modifiable('language'):
            for w in [lang_combo, lang_label]: w.setEnabled(False)
        def on_lang(x):
            lang_request = list(languages.keys())[lang_combo.currentIndex()]
            if lang_request != self.config.get('language'):
                self.config.set_key("language", lang_request, True)
                self.need_restart = True
        lang_combo.currentIndexChanged.connect(on_lang)

        nz_help = _('Number of zeros displayed after the decimal point. For example, if this is set to 2, "1." will be displayed as "1.00"')
        nz_label = HelpLabel(_('Zeros after decimal point') + ':', nz_help)
        nz = QSpinBox()
        nz.setMinimum(0)
        nz.setMaximum(self.config.decimal_point)
        nz.setValue(self.config.num_zeros)
        if not self.config.is_modifiable('num_zeros'):
            for w in [nz, nz_label]: w.setEnabled(False)
        def on_nz():
            value = nz.value()
            if self.config.num_zeros != value:
                self.config.num_zeros = value
                self.config.set_key('num_zeros', value, True)
                self.window.refresh_tabs()
        nz.valueChanged.connect(on_nz)

        # use_rbf = bool(self.config.get('use_rbf', True))
        # use_rbf_cb = QCheckBox(_('Use Replace-By-Fee'))
        # use_rbf_cb.setChecked(use_rbf)
        # use_rbf_cb.setToolTip(
        #     _('If you check this box, your transactions will be marked as non-final,') + '\n' + \
        #     _('and you will have the possibility, while they are unconfirmed, to replace them with transactions that pay higher fees.') + '\n' + \
        #     _('Note that some merchants do not accept non-final transactions until they are confirmed.'))
        # def on_use_rbf(x):
        #     self.config.set_key('use_rbf', bool(x))
        #     batch_rbf_cb.setEnabled(bool(x))
        # use_rbf_cb.stateChanged.connect(on_use_rbf)
        # tx_widgets.append((use_rbf_cb, None))

        # batch_rbf_cb = QCheckBox(_('Batch RBF transactions'))
        # batch_rbf_cb.setChecked(bool(self.config.get('batch_rbf', False)))
        # batch_rbf_cb.setEnabled(use_rbf)
        # batch_rbf_cb.setToolTip(
        #     _('If you check this box, your unconfirmed transactions will be consolidated into a single transaction.') + '\n' + \
        #     _('This will save fees.'))
        # def on_batch_rbf(x):
        #     self.config.set_key('batch_rbf', bool(x))
        # batch_rbf_cb.stateChanged.connect(on_batch_rbf)
        # tx_widgets.append((batch_rbf_cb, None))

        # lightning
        lightning_widgets = []

        help_recov = _(messages.MSG_RECOVERABLE_CHANNELS)
        recov_cb = QCheckBox(_("Create recoverable channels"))
        enable_toggle_use_recoverable_channels = bool(self.wallet.lnworker and self.wallet.lnworker.can_have_recoverable_channels())
        recov_cb.setEnabled(enable_toggle_use_recoverable_channels)
        recov_cb.setToolTip(messages.to_rtf(help_recov))
        recov_cb.setChecked(bool(self.config.get('use_recoverable_channels', True)) and enable_toggle_use_recoverable_channels)
        def on_recov_checked(x):
            self.config.set_key('use_recoverable_channels', bool(x))
        recov_cb.stateChanged.connect(on_recov_checked)

        help_trampoline = _(messages.MSG_HELP_TRAMPOLINE)
        trampoline_cb = QCheckBox(_("Use trampoline routing (disable gossip)"))
        trampoline_cb.setToolTip(messages.to_rtf(help_trampoline))
        trampoline_cb.setChecked(not bool(self.config.get('use_gossip', False)))
        def on_trampoline_checked(use_trampoline):
            use_gossip = not bool(use_trampoline)
            self.config.set_key('use_gossip', use_gossip)
            if use_gossip:
                self.window.network.start_gossip()
            else:
                self.window.network.run_from_another_thread(
                    self.window.network.stop_gossip())
            util.trigger_callback('ln_gossip_sync_progress')
            # FIXME: update all wallet windows
            util.trigger_callback('channels_updated', self.wallet)
        trampoline_cb.stateChanged.connect(on_trampoline_checked)

        help_instant_swaps = ' '.join([
            _("If this option is checked, your client will complete reverse swaps before the funding transaction is confirmed."),
            _("Note you are at risk of losing the funds in the swap, if the funding transaction never confirms.")
            ])
        instant_swaps_cb = QCheckBox(_("Allow instant swaps"))
        instant_swaps_cb.setToolTip(messages.to_rtf(help_instant_swaps))
        trampoline_cb.setChecked(not bool(self.config.get('allow_instant_swaps', False)))
        def on_instant_swaps_checked(allow_instant_swaps):
            self.config.set_key('allow_instant_swaps', bool(allow_instant_swaps))
        instant_swaps_cb.stateChanged.connect(on_instant_swaps_checked)

        help_remote_wt = ' '.join([
            _("A watchtower is a daemon that watches your channels and prevents the other party from stealing funds by broadcasting an old state."),
            _("If you have private a watchtower, enter its URL here."),
            _("Check our online documentation if you want to configure Electrum as a watchtower."),
        ])
        remote_wt_cb = QCheckBox(_("Use a remote watchtower"))
        remote_wt_cb.setToolTip('<p>'+help_remote_wt+'</p>')
        remote_wt_cb.setChecked(bool(self.config.get('use_watchtower', False)))
        def on_remote_wt_checked(x):
            self.config.set_key('use_watchtower', bool(x))
            self.watchtower_url_e.setEnabled(bool(x))
        remote_wt_cb.stateChanged.connect(on_remote_wt_checked)
        watchtower_url = self.config.get('watchtower_url')
        self.watchtower_url_e = QLineEdit(watchtower_url)
        self.watchtower_url_e.setEnabled(self.config.get('use_watchtower', False))
        def on_wt_url():
            url = self.watchtower_url_e.text() or None
            watchtower_url = self.config.set_key('watchtower_url', url)
        self.watchtower_url_e.editingFinished.connect(on_wt_url)

        msg = _('OpenAlias record, used to receive coins and to sign payment requests.') + '\n\n'\
              + _('The following alias providers are available:') + '\n'\
              + '\n'.join(['https://cryptoname.co/', 'http://xmr.link']) + '\n\n'\
              + 'For more information, see https://openalias.org'
        alias_label = HelpLabel(_('OpenAlias') + ':', msg)
        alias = self.config.get('alias','')
        self.alias_e = QLineEdit(alias)
        self.set_alias_color()
        self.alias_e.editingFinished.connect(self.on_alias_edit)

        msat_cb = QCheckBox(_("Show Lightning amounts with msat precision"))
        msat_cb.setChecked(bool(self.config.get('amt_precision_post_satoshi', False)))
        def on_msat_checked(v):
            prec = 3 if v == Qt.Checked else 0
            if self.config.amt_precision_post_satoshi != prec:
                self.config.amt_precision_post_satoshi = prec
                self.config.set_key('amt_precision_post_satoshi', prec)
                self.window.refresh_tabs()
        msat_cb.stateChanged.connect(on_msat_checked)

        # units
        units = base_units_list
        msg = (_('Base unit of your wallet.')
               + '\n1 RVN = 1000 mRVN. 1 mRVN = 1000 bits. 1 bit = 100 sat.\n'
               + _('This setting affects the Send tab, and all balance related fields.'))
        unit_label = HelpLabel(_('Base unit') + ':', msg)
        unit_combo = QComboBox()
        unit_combo.addItems(units)
        unit_combo.setCurrentIndex(units.index(self.window.base_unit()))
        def on_unit(x, nz):
            unit_result = units[unit_combo.currentIndex()]
            if self.window.base_unit() == unit_result:
                return
            edits = self.window.amount_e, self.window.receive_amount_e
            amounts = [edit.get_amount() for edit in edits]
            self.config.set_base_unit(unit_result)
            nz.setMaximum(self.config.decimal_point)
            self.window.update_tabs()
            for edit, amount in zip(edits, amounts):
                edit.setAmount(amount)
            self.window.update_status()
        unit_combo.currentIndexChanged.connect(lambda x: on_unit(x, nz))

        thousandsep_cb = QCheckBox(_("Add thousand separators to bitcoin amounts"))
        thousandsep_cb.setChecked(bool(self.config.get('amt_add_thousands_sep', False)))
        def on_set_thousandsep(v):
            checked = v == Qt.Checked
            if self.config.amt_add_thousands_sep != checked:
                self.config.amt_add_thousands_sep = checked
                self.config.set_key('amt_add_thousands_sep', checked)
                self.window.refresh_tabs()
        thousandsep_cb.stateChanged.connect(on_set_thousandsep)

        qr_combo = QComboBox()
        qr_combo.addItem("Default", "default")
        msg = (_("For scanning QR codes.") + "\n"
               + _("Install the zbar package to enable this."))
        qr_label = HelpLabel(_('Video Device') + ':', msg)
        from .qrreader import find_system_cameras
        system_cameras = find_system_cameras()
        for cam_desc, cam_path in system_cameras.items():
            qr_combo.addItem(cam_desc, cam_path)
        index = qr_combo.findData(self.config.get("video_device"))
        qr_combo.setCurrentIndex(index)
        on_video_device = lambda x: self.config.set_key("video_device", qr_combo.itemData(x), True)
        qr_combo.currentIndexChanged.connect(on_video_device)

        colortheme_combo = QComboBox()
        colortheme_combo.addItem(_('Light'), 'default')
        colortheme_combo.addItem(_('Dark'), 'dark')
        index = colortheme_combo.findData(self.config.get('qt_gui_color_theme', 'dark'))
        colortheme_combo.setCurrentIndex(index)
        colortheme_label = QLabel(_('Color theme') + ':')
        def on_colortheme(x):
            self.config.set_key('qt_gui_color_theme', colortheme_combo.itemData(x), True)
            #self.window.gui_object.reload_app_stylesheet()
            self.need_restart = True
        colortheme_combo.currentIndexChanged.connect(on_colortheme)

        updatecheck_cb = QCheckBox(_("Automatically check for software updates"))
        updatecheck_cb.setChecked(bool(self.config.get('check_updates', False)))
        def on_set_updatecheck(v):
            self.config.set_key('check_updates', v == Qt.Checked, save=True)
        updatecheck_cb.stateChanged.connect(on_set_updatecheck)

        filelogging_cb = QCheckBox(_("Write logs to file"))
        filelogging_cb.setChecked(bool(self.config.get('log_to_file', True)))
        def on_set_filelogging(v):
            self.config.set_key('log_to_file', v == Qt.Checked, save=True)
            self.need_restart = True
        filelogging_cb.stateChanged.connect(on_set_filelogging)
        filelogging_cb.setToolTip(_('Debug logs can be persisted to disk. These are useful for troubleshooting.'))

        preview_cb = QCheckBox(_('Advanced preview'))
        preview_cb.setChecked(bool(self.config.get('advanced_preview', False)))
        preview_cb.setToolTip(_("Open advanced transaction preview dialog when 'Pay' is clicked."))
        def on_preview(x):
            self.config.set_key('advanced_preview', x == Qt.Checked)
        preview_cb.stateChanged.connect(on_preview)

        usechange_cb = QCheckBox(_('Use change addresses'))
        usechange_cb.setChecked(self.window.wallet.use_change)
        if not self.config.is_modifiable('use_change'): usechange_cb.setEnabled(False)
        def on_usechange(x):
            usechange_result = x == Qt.Checked
            if self.window.wallet.use_change != usechange_result:
                self.window.wallet.use_change = usechange_result
                self.window.wallet.db.put('use_change', self.window.wallet.use_change)
                multiple_cb.setEnabled(self.window.wallet.use_change)
        usechange_cb.stateChanged.connect(on_usechange)
        usechange_cb.setToolTip(_('Using change addresses makes it more difficult for other people to track your transactions.'))

        def on_multiple(x):
            multiple = x == Qt.Checked
            if self.wallet.multiple_change != multiple:
                self.wallet.multiple_change = multiple
                self.wallet.db.put('multiple_change', multiple)
        multiple_change = self.wallet.multiple_change
        multiple_cb = QCheckBox(_('Use multiple change addresses'))
        multiple_cb.setEnabled(self.wallet.use_change)
        multiple_cb.setToolTip('\n'.join([
            _('In some cases, use up to 3 change addresses in order to break '
              'up large coin amounts and obfuscate the recipient address.'),
            _('This may result in higher transactions fees.')
        ]))
        multiple_cb.setChecked(multiple_change)
        multiple_cb.stateChanged.connect(on_multiple)

        def fmt_docs(key, klass):
            lines = [ln.lstrip(" ") for ln in klass.__doc__.split("\n")]
            return '\n'.join([key, "", " ".join(lines)])

        choosers = sorted(coinchooser.COIN_CHOOSERS.keys())
        if len(choosers) > 1:
            chooser_name = coinchooser.get_name(self.config)
            msg = _('Choose coin (UTXO) selection method.  The following are available:\n\n')
            msg += '\n\n'.join(fmt_docs(*item) for item in coinchooser.COIN_CHOOSERS.items())
            chooser_label = HelpLabel(_('Coin selection') + ':', msg)
            chooser_combo = QComboBox()
            chooser_combo.addItems(choosers)
            i = choosers.index(chooser_name) if chooser_name in choosers else 0
            chooser_combo.setCurrentIndex(i)
            def on_chooser(x):
                chooser_name = choosers[chooser_combo.currentIndex()]
                self.config.set_key('coin_chooser', chooser_name)
            chooser_combo.currentIndexChanged.connect(on_chooser)

        def on_unconf(x):
            self.config.set_key('confirmed_only', bool(x))
        conf_only = bool(self.config.get('confirmed_only', False))
        unconf_cb = QCheckBox(_('Spend only confirmed coins'))
        unconf_cb.setToolTip(_('Spend only confirmed inputs.'))
        unconf_cb.setChecked(conf_only)
        unconf_cb.stateChanged.connect(on_unconf)

        def on_outrounding(x):
            self.config.set_key('coin_chooser_output_rounding', bool(x))
        enable_outrounding = bool(self.config.get('coin_chooser_output_rounding', False))
        outrounding_cb = QCheckBox(_('Enable output value rounding'))
        outrounding_cb.setToolTip(
            _('Set the value of the change output so that it has similar precision to the other outputs.') + '\n' +
            _('This might improve your privacy somewhat.') + '\n' +
            _('If enabled, at most 100 satoshis might be lost due to this, per transaction.'))
        outrounding_cb.setChecked(enable_outrounding)
        outrounding_cb.stateChanged.connect(on_outrounding)

        def on_msgs(x):
            self.config.set_key('enable_op_return_messages', bool(x))
        enable_tx_custom_message = bool(self.config.get('enable_op_return_messages', False))
        tx_custom_message = QCheckBox(_('Enable OP_RETURN messages'))
        tx_custom_message.setToolTip(
            _('Add the ability to add an invalid pubkey to a transaction') + '\n' +
            _('that has been encoded with a short message.') + '\n' +
            _('This is not typical Ravencoin behavior and these messages') + '\n' +
            _('may be pruned from the chain in the future.') + '\n' +
            _('This will increase your transaction size and therefore your fee.'))
        tx_custom_message.setChecked(enable_tx_custom_message)
        tx_custom_message.stateChanged.connect(on_msgs)
        tx_widgets.append((tx_custom_message, None))

        block_explorers = sorted(util.block_explorer_info().keys())
        BLOCK_EX_CUSTOM_ITEM = _("Custom URL")
        if BLOCK_EX_CUSTOM_ITEM in block_explorers:  # malicious translation?
            block_explorers.remove(BLOCK_EX_CUSTOM_ITEM)
        block_explorers.append(BLOCK_EX_CUSTOM_ITEM)
        msg = _('Choose which online block explorer to use for functions that open a web browser')
        block_ex_label = HelpLabel(_('Online Block Explorer') + ':', msg)
        block_ex_combo = QComboBox()
        block_ex_custom_e = QLineEdit(str(self.config.get('block_explorer_custom') or ''))
        block_ex_combo.addItems(block_explorers)
        block_ex_combo.setCurrentIndex(
            block_ex_combo.findText(util.block_explorer(self.config) or BLOCK_EX_CUSTOM_ITEM))
        def showhide_block_ex_custom_e():
            block_ex_custom_e.setVisible(block_ex_combo.currentText() == BLOCK_EX_CUSTOM_ITEM)
        showhide_block_ex_custom_e()
        def on_be_combo(x):
            if block_ex_combo.currentText() == BLOCK_EX_CUSTOM_ITEM:
                on_be_edit()
            else:
                be_result = block_explorers[block_ex_combo.currentIndex()]
                self.config.set_key('block_explorer_custom', None, False)
                self.config.set_key('block_explorer', be_result, True)
            showhide_block_ex_custom_e()
        block_ex_combo.currentIndexChanged.connect(on_be_combo)
        def on_be_edit():
            val = block_ex_custom_e.text()
            try:
                val = ast.literal_eval(val)  # to also accept tuples
            except:
                pass
            self.config.set_key('block_explorer_custom', val)
        block_ex_custom_e.editingFinished.connect(on_be_edit)
        block_ex_hbox = QHBoxLayout()
        block_ex_hbox.setContentsMargins(0, 0, 0, 0)
        block_ex_hbox.setSpacing(0)
        block_ex_hbox.addWidget(block_ex_combo)
        block_ex_hbox.addWidget(block_ex_custom_e)
        block_ex_hbox_w = QWidget()
        block_ex_hbox_w.setLayout(block_ex_hbox)

        ipfs_explorers = sorted(util.ipfs_explorer_info().keys())
        IPFS_EX_CUSTOM_ITEM = _("Custom URL")
        if IPFS_EX_CUSTOM_ITEM in ipfs_explorers:  # malicious translation?
            ipfs_explorers.remove(IPFS_EX_CUSTOM_ITEM)
        ipfs_explorers.append(IPFS_EX_CUSTOM_ITEM)
        msg = _('Choose which online IPFS explorer to use for functions that open a web browser')
        ipfs_ex_label = HelpLabel(_('Online IPFS Explorer') + ':', msg)
        ipfs_ex_combo = QComboBox()
        ipfs_ex_custom_e = QLineEdit(self.config.get('ipfs_explorer_custom') or '')
        ipfs_ex_combo.addItems(ipfs_explorers)
        ipfs_ex_combo.setCurrentIndex(
            ipfs_ex_combo.findText(util.ipfs_explorer(self.config) or IPFS_EX_CUSTOM_ITEM))

        def showhide_ipfs_ex_custom_e():
            ipfs_ex_custom_e.setVisible(ipfs_ex_combo.currentText() == IPFS_EX_CUSTOM_ITEM)

        showhide_ipfs_ex_custom_e()

        def on_ie_combo(x):
            if ipfs_ex_combo.currentText() == IPFS_EX_CUSTOM_ITEM:
                on_ie_edit()
            else:
                ie_result = ipfs_explorers[ipfs_ex_combo.currentIndex()]
                self.config.set_key('ipfs_explorer_custom', None, False)
                self.config.set_key('ipfs_explorer', ie_result, True)
            showhide_ipfs_ex_custom_e()

        ipfs_ex_combo.currentIndexChanged.connect(on_ie_combo)

        def on_ie_edit():
            val = ipfs_ex_custom_e.text()
            try:
                val = ast.literal_eval(val)  # to also accept tuples
            except:
                pass
            self.config.set_key('ipfs_explorer_custom', val)

        ipfs_ex_custom_e.editingFinished.connect(on_ie_edit)
        ipfs_ex_hbox = QHBoxLayout()
        ipfs_ex_hbox.setContentsMargins(0, 0, 0, 0)
        ipfs_ex_hbox.setSpacing(0)
        ipfs_ex_hbox.addWidget(ipfs_ex_combo)
        ipfs_ex_hbox.addWidget(ipfs_ex_custom_e)
        ipfs_ex_hbox_w = QWidget()
        ipfs_ex_hbox_w.setLayout(ipfs_ex_hbox)
        tx_widgets.append((ipfs_ex_label, ipfs_ex_hbox_w))

        # Fiat Currency
        hist_checkbox = QCheckBox()
        hist_capgains_checkbox = QCheckBox()
        fiat_address_checkbox = QCheckBox()
        ccy_combo = QComboBox()
        ex_combo = QComboBox()

        def update_currencies():
            if not self.window.fx: return
            currencies = sorted(self.fx.get_currencies(self.fx.get_history_config()))
            ccy_combo.clear()
            ccy_combo.addItems([_('None')] + currencies)
            if self.fx.is_enabled():
                ccy_combo.setCurrentIndex(ccy_combo.findText(self.fx.get_currency()))

        def update_history_cb():
            if not self.fx: return
            hist_checkbox.setChecked(self.fx.get_history_config())
            hist_checkbox.setEnabled(self.fx.is_enabled())

        def update_fiat_address_cb():
            if not self.fx: return
            fiat_address_checkbox.setChecked(self.fx.get_fiat_address_config())

        def update_history_capgains_cb():
            if not self.fx: return
            hist_capgains_checkbox.setChecked(self.fx.get_history_capital_gains_config())
            hist_capgains_checkbox.setEnabled(hist_checkbox.isChecked())

        def update_exchanges():
            if not self.fx: return
            b = self.fx.is_enabled()
            ex_combo.setEnabled(b)
            if b:
                h = self.fx.get_history_config()
                c = self.fx.get_currency()
                exchanges = self.fx.get_exchanges_by_ccy(c, h)
            else:
                exchanges = self.fx.get_exchanges_by_ccy('USD', False)
            ex_combo.blockSignals(True)
            ex_combo.clear()
            ex_combo.addItems(sorted(exchanges))
            ex_combo.setCurrentIndex(ex_combo.findText(self.fx.config_exchange()))
            ex_combo.blockSignals(False)

        def on_currency(hh):
            if not self.fx: return
            b = bool(ccy_combo.currentIndex())
            ccy = str(ccy_combo.currentText()) if b else None
            self.fx.set_enabled(b)
            if b and ccy != self.fx.ccy:
                self.fx.set_currency(ccy)
            update_history_cb()
            update_exchanges()
            self.window.update_fiat()

        def on_exchange(idx):
            exchange = str(ex_combo.currentText())
            if self.fx and self.fx.is_enabled() and exchange and exchange != self.fx.exchange.name():
                self.fx.set_exchange(exchange)

        def on_history(checked):
            if not self.fx: return
            self.fx.set_history_config(checked)
            update_exchanges()
            self.window.history_model.refresh('on_history')
            if self.fx.is_enabled() and checked:
                self.fx.trigger_update()
            update_history_capgains_cb()

        def on_history_capgains(checked):
            if not self.fx: return
            self.fx.set_history_capital_gains_config(checked)
            self.window.history_model.refresh('on_history_capgains')

        def on_fiat_address(checked):
            if not self.fx: return
            self.fx.set_fiat_address_config(checked)
            self.window.address_list.refresh_headers()
            self.window.address_list.update()

        update_currencies()
        update_history_cb()
        update_history_capgains_cb()
        update_fiat_address_cb()
        update_exchanges()
        ccy_combo.currentIndexChanged.connect(on_currency)
        hist_checkbox.stateChanged.connect(on_history)
        hist_capgains_checkbox.stateChanged.connect(on_history_capgains)
        fiat_address_checkbox.stateChanged.connect(on_fiat_address)
        ex_combo.currentIndexChanged.connect(on_exchange)

        gui_widgets = []
        gui_widgets.append((lang_label, lang_combo))
        gui_widgets.append((colortheme_label, colortheme_combo))
        gui_widgets.append((unit_label, unit_combo))
        gui_widgets.append((nz_label, nz))
        gui_widgets.append((msat_cb, None))
        gui_widgets.append((thousandsep_cb, None))
        tx_widgets = []
        tx_widgets.append((usechange_cb, None))
        #tx_widgets.append((use_rbf_cb, None))
        #tx_widgets.append((batch_rbf_cb, None))
        tx_widgets.append((preview_cb, None))
        tx_widgets.append((unconf_cb, None))
        tx_widgets.append((multiple_cb, None))
        tx_widgets.append((outrounding_cb, None))
        if len(choosers) > 1:
            tx_widgets.append((chooser_label, chooser_combo))
        tx_widgets.append((block_ex_label, block_ex_hbox_w))
        lightning_widgets = []
        lightning_widgets.append((recov_cb, None))
        lightning_widgets.append((trampoline_cb, None))
        lightning_widgets.append((instant_swaps_cb, None))
        lightning_widgets.append((remote_wt_cb, self.watchtower_url_e))
        fiat_widgets = []
        fiat_widgets.append((QLabel(_('Fiat currency')), ccy_combo))
        fiat_widgets.append((QLabel(_('Source')), ex_combo))
        fiat_widgets.append((QLabel(_('Show history rates')), hist_checkbox))
        fiat_widgets.append((QLabel(_('Show capital gains in history')), hist_capgains_checkbox))
        fiat_widgets.append((QLabel(_('Show Fiat balance for addresses')), fiat_address_checkbox))
        misc_widgets = []
        misc_widgets.append((updatecheck_cb, None))
        misc_widgets.append((filelogging_cb, None))
        misc_widgets.append((alias_label, self.alias_e))
        misc_widgets.append((qr_label, qr_combo))

        # Asset black list
        msg = 'A list of regular expressions separated by new lines. ' \
              'If an asset\'s name matches any regular expression in this list, ' \
              'it will be hidden from view.'
        regex_b = '\n'.join(self.window.asset_blacklist)
        blacklist_info = HelpLabel(_('Asset Blacklist') + ':', msg)
        regex_e_b = QTextEdit()
        regex_e_b.setLineWrapMode(QTextEdit.NoWrap)
        regex_e_b.setPlainText(regex_b)

        def update_blacklist():
            self.window.asset_blacklist = regex_e_b.toPlainText().split('\n')
            if not self.window.asset_blacklist[0]: # We don't want an empty string, we want an empty regex
                self.window.asset_blacklist = []
            self.save_blacklist = True

        regex_e_b.textChanged.connect(update_blacklist)
        asset_widgets.append((blacklist_info, regex_e_b))

        # Asset white list
        msg = 'A list of regular expressions seperated by new lines. ' \
              'Assets that match any of these regular expressions and would normally ' \
              'be blocked by the blacklist are shown.'
        regex_w = '\n'.join(self.window.asset_whitelist)
        whitelist_info = HelpLabel(_('Asset Whitelist') + ':', msg)
        regex_e_w = QTextEdit()
        regex_e_w.setLineWrapMode(QTextEdit.NoWrap)
        regex_e_w.setPlainText(regex_w)

        def update_whitelist():
            self.window.asset_whitelist = regex_e_w.toPlainText().split('\n')
            if not self.window.asset_whitelist[0]:
                self.window.asset_whitelist = []
            self.save_whitelist = True

        regex_e_w.textChanged.connect(update_whitelist)
        asset_widgets.append((whitelist_info, regex_e_w))

        show_spam_cb = QCheckBox(_("Show assets hidden from view"))
        show_spam_cb.setChecked(self.config.get('show_spam_assets', False))

        def on_set_show_spam(v):
            self.window.config.set_key('show_spam_assets', v == Qt.Checked, save=True)
            self.window.asset_list.update()
            self.window.history_model.refresh('Toggled show spam assets', True)

        show_spam_cb.stateChanged.connect(on_set_show_spam)
        asset_widgets.append((show_spam_cb, None))

        advanced_assets_cb = QCheckBox(_("Enable advanced asset options"))
        advanced_assets_cb.setChecked(self.config.get('advanced_asset_functions', False))

        def on_set_advanced_assets_cb(v):
            self.window.config.set_key('advanced_asset_functions', v == Qt.Checked, save=True)

            self.window.create_workspace.associated_data_interpret_override.setVisible(v == Qt.Checked)
            self.window.create_workspace.asset_addr_w.setVisible(v == Qt.Checked)
            self.window.reissue_workspace.associated_data_interpret_override.setVisible(v == Qt.Checked)
            self.window.reissue_workspace.asset_addr_w.setVisible(v == Qt.Checked)
            self.window.asset_list.update()

        advanced_assets_cb.stateChanged.connect(on_set_advanced_assets_cb)
        asset_widgets.append((advanced_assets_cb, None))

        message_widgets = []

        dev_notifications_cb = QCheckBox(_("Enable developer notifications"))
        dev_notifications_cb.setChecked(self.config.get('get_dev_notifications', True))

        def on_set_dev_notifications_cb(v):
            self.window.config.set_key('get_dev_notifications', v == Qt.Checked, save=True)
            self.window.message_list.update()

        dev_notifications_cb.stateChanged.connect(on_set_dev_notifications_cb)
        message_widgets.append((dev_notifications_cb, None))

        tabs_info = [
            (gui_widgets, _('Appearance')),
            (asset_widgets, _('Assets')),
            (tx_widgets, _('Transactions')),
            # (lightning_widgets, _('Lightning')),
            (fiat_widgets, _('Fiat')),
            (message_widgets, _('Messages')),
            (oa_widgets, _('OpenAlias')),
            (misc_widgets, _('Misc')),
        ]
        for widgets, name in tabs_info:
            tab = QWidget()
            tab_vbox = QVBoxLayout(tab)
            grid = QGridLayout()
            for a,b in widgets:
                i = grid.rowCount()
                if b:
                    if a:
                        grid.addWidget(a, i, 0)
                    grid.addWidget(b, i, 1)
                else:
                    grid.addWidget(a, i, 0, 1, 2)
            tab_vbox.addLayout(grid)
            tab_vbox.addStretch(1)
            tabs.addTab(tab, name)

        vbox.addWidget(tabs)
        vbox.addStretch(1)
        vbox.addLayout(Buttons(CloseButton(self)))
        self.setLayout(vbox)
        
    def set_alias_color(self):
        if not self.config.get('alias'):
            self.alias_e.setStyleSheet("")
            return
        if self.window.alias_info:
            alias_addr, alias_name, validated = self.window.alias_info
            self.alias_e.setStyleSheet((ColorScheme.GREEN if validated else ColorScheme.RED).as_stylesheet(True))
        else:
            self.alias_e.setStyleSheet(ColorScheme.RED.as_stylesheet(True))

    def on_alias_edit(self):
        self.alias_e.setStyleSheet("")
        alias = str(self.alias_e.text())
        self.config.set_key('alias', alias, True)
        if alias:
            self.window.fetch_alias()
